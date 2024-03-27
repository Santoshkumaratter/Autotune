from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import render
from django.http import JsonResponse

import json
import logging

import coloredlogs
import dirtyjson
import langchain
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema.messages import SystemMessage
from pydantic import BaseModel, Field

# setup loggers
logger = logging.getLogger(__name__)
coloredlogs.install(logger=logger)
logger.propagate = False

langchain.debug = False


class GenerateRobustSamples(APIView):
    def parse(self, output, parser, question=False):
        parsed = dirtyjson.loads(output)
        if question:
            parsed = parsed["qna"]
        else:
            parsed = list(parsed)
        data = []
        for i in parsed:
            try:
                parser.parse(json.dumps(dict(i)))
                data.append(dict(i))
            except Exception as e:
                logger.error(e, dict(i))
        return data

    async def post(self, request):
        try:
            data = request.data
            api_key = data['api_key']
            labels = data['labels']
            num_samples = data['num_samples']
            valid_data = data.get('valid_data', None)
            invalid_data = data.get('invalid_data', None)

            res = await self.generate(
                labels,
                api_key,
                num_samples,
                valid_data=valid_data,
                invalid_data=invalid_data,
            )
            return Response(res, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error %e", e)
            return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def generate(self, labels, api_key, num_samples, valid_data=None, invalid_data=None):
        class LabeledDataset(BaseModel):
            text: str = Field(..., description="The text of the sample generated")
            label: str = Field(
                ..., description="The label of the sample generated. Valid labels are {labels}".format(labels=labels),
            )

        parser = PydanticOutputParser(pydantic_object=LabeledDataset)

        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            openai_api_key=api_key,
            max_tokens=None,
            temperature=1,
        )

        user_content = f"Generate {num_samples} robust samples"
        template = ""

        if valid_data:
            valid_data = json.dumps(valid_data, separators=(",", ":")).replace("},", "},\n")
            template = template + f"The correctly labeled data is \n {valid_data}. \n "
        if invalid_data:
            invalid_data = json.dumps(invalid_data, separators=(",", ":")).replace("},", "},\n")
            template = template + f"The incorrectly labeled data is \n {invalid_data}.\n "

        template += (
            f"{parser.get_format_instructions()} \n {user_content}. \n The valid labels are {labels}. \n "
            "Provide an output that can be directly parsed by json.loads and provide JSON only. NO CONTEXT."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=(
                        "You are a helpful data generation assistant. You generate labeled data for other models to learn from."
                        "You only generate data for 'valid labels' that you are given. You are given a question and a list of valid labels."
                        "You maybe also be given a list of correctly labeled data and incorrectly labeled data. You use these to improve the data generation."
                        "The data generated should be in the format of a list of dictionaries, where each dictionary has the keys 'text' and 'label'."
                        "You enclose the JSON values with double quotes"
                    )
                ),
                HumanMessagePromptTemplate.from_template(template),
            ]
        )

        chain = LLMChain(llm=llm, prompt=prompt, verbose=True)

        output = await chain.arun(
            text=user_content,
            labels=labels,
            invalid_data=invalid_data,
            valid_data=valid_data,
            format_instructions=parser.get_format_instructions(),
        )

        try:
            parsed = self.parse(output, parser)
            if len(parsed) < num_samples:
                logger.error("Only got %d responses", len(parsed))
        except Exception as e:
            logger.error("Exception in parsing %s", str(e))
            logger.error("Corrupted JSON: " + output)
            parsed = []

        return parsed


class QuestionDataset(BaseModel):
    set: str = Field(..., description="The generated words")


class GenerateQuestions(APIView):
    async def post(self, request):
        try:
            data = request.data
            api_key = data['api_key']
            num_samples = data['num_samples']
            content_array = data['content_array']
            model = data.get('model', "gpt-3.5-turbo")
            system_prompt = data.get('system_prompt', None)
            user_prompt = data.get('user_prompt', None)

            res = await self.generate_questions(
                api_key, num_samples, content_array, model, system_prompt, user_prompt
            )
            return Response(res, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error("Error %e", e)
            return Response({'error': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def generate_questions(
            self, api_key, num_samples, content_array, model, system_prompt=None, user_prompt=None
    ):
        parser = PydanticOutputParser(pydantic_object=QuestionDataset)

        llm = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            max_tokens=None,
            temperature=1,
        )

        user_content = f"Generate {num_samples} robust samples"
        if user_prompt:
            template = ""
            template = user_prompt

            for content in content_array:
                template = template + f"{content} \n \n"

        else:
            template = ""
            template = template + "Required Output: \n"

            template = (
                    template
                    + "Your task is to analyize the following text and generate questions and answers.\n\n\n"
            )

            for content in content_array:
                template = template + f"{content} \n \n"

            template = (
                    template
                    + " The questions generated shoud be UNIQUE, CRYSTAL CLEAR, and INDEPENDANT of the text given. Use PRECISE TERMS in the questions \n"
            )
            template = (
                    template
                    + " Don't have terms which reference the text. Questions should be understood by a 3rd party with no context.\n"
            )
            template = (
                    template
                    + "Keep the answers to the questions detailed. Avoid one word answers. Add all relelvant information to the answer. \n"
            )
            template = (
                    template
                    + "Answer as a leading industry expert explaining to a 7year old with no understanding of the question. \n"
            )
            template = (
                    template
                    + "Provide an output that can be directly parsed by `json.loads` and provide JSON output only. NO CONTEXT."
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=system_prompt
                    if system_prompt
                    else (
                        "You are a helpful data generation assistant.You create questions that are answered by an answer that combines information from a chunk of data"
                        "You create a set of questions and answers based on the given text assuming they will be asked by a farmer. You are an expert in this field"
                        "Each question should closely match the language, terminology, and key phrases used in the text to ensure a high content overlap."
                        "Focus on extracting and reformulating specific sentences or phrases from the text as questions, and provide direct quotes or slight rephrasings from the text as answers."
                        "Ask questions that have longer answers. Keep the answers verbose."
                        "Aim for a content overlap of about 90%. Overlap is defined as the entire overlap with all the questions stating the coverage of the over Q and A with the text."
                        "You enclose the JSON values with double quotes ALWAYS."
                        "Don't say terms like 'as mentioned in the text'."
                        "The Questions should not contain vague terms like 'process' or 'programme' or 'product'."
                        "Don't reference images like 'Fig. 29.1'. Generate questions independent of such lines"
                        "Use complete terms in the questions and answers.  Don't assume the reader to have reference to anything other than the question."
                        "The Required Ouput JSON format is as follows: \n"
                        "{ \n"
                        '   "qna": [ \n'
                        "       { \n"
                        '           "question": "<QUESTION_TEXT>", \n'
                        '           "answer": "<ANSWER_TEXT>" \n'
                        "       }, \n"
                        "       ... \n"
                        "   ] \n"
                        "}"
                    )
                ),
                HumanMessagePromptTemplate.from_template(template),
            ]
        )

        chain = LLMChain(llm=llm, prompt=prompt, verbose=True)

        output = await chain.arun(
            text=user_content,
            content=content_array[0],
            format_instructions=parser.get_format_instructions(),
        )

        logger.info(f"this is the output: \n{output}")

        try:
            parsed = self.parse(output, parser, True)
            if len(parsed) < num_samples:
                logger.error("Only got %d responses", len(parsed))
        except Exception as e:
            logger.error("Exception in parsing %s", str(e))
            logger.error("Corrupted JSON: " + output)
            parsed = []

        return parsed


def split_data(res, split):
    assert sum(split) == 100, "Split should sum to 100"
    train_end = int(len(res) * split[0] / 100)
    val_end = train_end + int(len(res) * split[1] / 100)
    test_end = val_end + int(len(res) * split[2] / 100)
    train = res[:train_end]
    val = res[train_end:val_end]
    test = res[val_end:test_end]
    return train, val, test
