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
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# Set debug mode for langchain
langchain.debug = False

# Setup logger
logger = logging.getLogger(__name__)
coloredlogs.install(logger=logger)
logger.propagate = False

# Define parsing function
def parse(output, parser, question=False):
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

async def generate(
    labels,
    api_key,
    num_samples,
    model="gpt-3.5-turbo",
    temperature=1,
    max_tokens=None,
    valid_data=None,
    invalid_data=None,
):
    class LabeledDataset(BaseModel):
        text: str = Field(..., description="The text of the sample generated")
        label: str = Field(
            ..., description=f"The label of the sample generated. Valid labels are {labels}"
        )

    parser = PydanticOutputParser(pydantic_object=LabeledDataset)

    llm = ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    user_content = f"Generate {num_samples} robust samples"
    template = ""

    if valid_data:
        valid_data = json.dumps(valid_data, separators=(",", ":")).replace("},", "},\n")
        template += f"The correctly labeled data is \n{valid_data}. \n"
    if invalid_data:
        invalid_data = json.dumps(invalid_data, separators=(",", ":")).replace("},", "},\n")
        template += f"The incorrectly labeled data is \n{invalid_data}.\n"

    template += "{format_instructions} \n{text}. \n The valid labels are {labels}. \n"
    template += "Provide an output that can be directly parsed by json.loads and provide JSON only. NO CONTEXT."

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "You are a helpful data generation assistant. You generate labeled data for other models to learn "
                    "from."
                    "You only generate data for 'valid labels' that you are given. You are given a question and a "
                    "list of valid labels."
                    "You maybe also be given a list of correctly labeled data and incorrectly labeled data. You use "
                    "these to improve the data generation."
                    "The data generated should be in the format of a list of dictionaries, where each dictionary has "
                    "the keys 'text' and 'label'."
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
        parsed = parse(output, parser)
        if len(parsed) < num_samples:
            logger.error("Only got %d responses", len(parsed))
    except Exception as e:
        logger.error("Exception in parsing %s", str(e))
        logger.error("Corrupted JSON: " + output)
        parsed = []

    return parsed

class get_data(APIView):
    async def post(self, request):
        try:
            labels = request.data.get("labels")
            api_key = request.data.get("api_key")
            num_samples = request.data.get("num_samples")
            valid_data = request.data.get("valid_data")
            invalid_data = request.data.get("invalid_data")

            if not (labels and api_key and num_samples):
                return Response({"error": "Labels, API key, and number of samples are required"}, status=status.HTTP_400_BAD_REQUEST)

            generated_data = await generate(
                labels=labels,
                api_key=api_key,
                num_samples=num_samples,
                valid_data=valid_data,
                invalid_data=invalid_data
            )

            return Response({"data": generated_data}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("Error occurred: %s", str(e))
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
