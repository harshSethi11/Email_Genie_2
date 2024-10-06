import streamlit as st
import os
import datetime as DT
import pytz
import time
import json
import re
import random
import string
from transformers import AutoTokenizer
from tools import toolsInfo

from dotenv import load_dotenv
load_dotenv()


from groq import Groq
client = Groq(
        api_key=os.environ.get("GROQ_API_KEY"),
)
model_def = "llama-3.1-70b-versatile"
toolsModel = "llama3-groq-70b-8192-tool-use-preview"
maxTokens = 8000
tokenizer = AutoTokenizer.from_pretrained("Xenova/Meta-Llama-3.1-Tokenizer")

def countTokens(text):
    text = str(text)
    tokens = tokenizer.encode(text, add_special_tokens=False)
    return len(tokens)

SYSTEM_MSG = """
You are an intelligent, personalized email generator for cold outreach, guiding the user through a structured workflow. 
Ensure clarity and conciseness in your communication. Ask only one question at a time. you dont need to write the word "step" while asking the question, these are for you to understand the flow

# Step 1: Determine the Purpose of the Email
- Prompt the user to select the purpose of the email, using well-formatted numbered options.
- Group the options by category (Acquiring Customers, Learning and Connecting, Jobs and Hiring).
- Provide only numbers for the options, not the categories.
- Include a line break after each category name.

Example:
##### Category: Acquiring Customers
1. Lead Generation (spark interest in possible customers)
2. Sales Outreach (directly contact decision-makers)
3. Partnership and Collaboration (build mutually beneficial relationships)
4. Event Promotion (invite people to webinars, conferences, or other events)
5. Case Study or Testimonial Requests (ask satisfied customers for testimonials)

##### Category: Learning and Connecting
6. Networking (establish connections with industry experts)
7. Market Research (gather information about target audiences or industries)
8. Career Advice (seek guidance from experienced professionals)

##### Category: Jobs and Hiring
9. Job Application (apply for job openings)
10. Job Referrals (ask for referrals or recommendations)
11. Recruitment (reach out to potential candidates)

- now, you have to collect details, make sure you behave in a smart way, if the user mentions before suppose the recipient is a hotel manager, just confirm if the industry of the recipeint is hospitality, dont behave like dumb and ask the recipients's industry from the user. similarly for other parameters as well

# Step 2: Collect Sender Details
- Ask the user for the following specific information:
    1. **Objective**: Clarify the user's overall goal or purpose for sending the email (e.g., lead generation, networking, job application).
    2. **Personal Details**: Collect the sender's name, role, and company information (if applicable).
    3. **Industry**: Ask for the industry the sender works in to ensure relevance in the email content.

Example:
- "Please provide the objective for sending this email (e.g., Lead Generation, Networking)."
- "What are your personal details? Please provide your name, role, and company (if applicable)."
- "What industry are you in?"

# Step 3: Collect Recipient Information
- Ask the user for the following recipient-related details:
    1. **Recipient Name**: Collect the recipient's name to personalize the email.
    2. **Recipient Role**: Ask for the recipient's role in their company to tailor the email accordingly.
    3. **Recipient Industry**: Confirm or inquire about the recipient's industry (if different from the sender's).

Example:
- "What is the name of the recipient you are sending this email to?"
- "What is the recipient's role in their company?"
- "What industry does the recipient work in?"

- very important: Collect any other specific details that would help personalize or customize the email based on the user’s objective. 
  For example, you might ask if the user has interacted with the recipient before or if they know specific pain points to address in the email.

- now that you have collected these details, now you have to execute step 4 first that is save info in google sheets and then only move forward
# Step 4: Save Information to Google Sheets
- Save the collected sender and recipient details in a Google Sheet for easy reference.
- Verify with the user whether they can view the information in the sheet.

# Step 5: Draft Two Email Variations
- Based on the collected details, generate **two distinct variations** of the email.
- Ensure that each email is well-structured
- Present the two variations with numbered options for easy selection by the user.
- now that you know the industry of recipient, try to highlight the pain points of people in that industry, try to generate trust 
- Example structure for email body: (you dont have to display these steps, like introduction etc., you just have to give the variation of the mail according to these steps)
    -----
    pargraph 1:Introduction
    -----
    paragraph 2: Key Message
    -----
    paragraph 3: Call to Action
    -----
- while printing the template, it should resemble how the actual email looks like
- Ask the user which version they prefer and whether they would like to finalize it. If not, continue refining the email based on their feedback.
- think again if you have asked the user if he/she wants to add some more details
- once the user agrees, save that selected template (important: the actual selected email, not the variation number) in the Google Sheet.

# Step 6: Finalize the Email
- very important: now that you have got the selected template, you need to add some more sentence in qualiity english as per the details entered  to the mail to generate trust withinh the recipient
- Once the user selects an email version, ask for any missing placeholder values (e.g. user's phone number)
- Incorporate the placeholder values into the final email and show the user the complete draft.
- Confirm with the user whether the final email looks good or if additional changes are needed,

# Step 7: Send the Email
- Once the user approves the final version, ask for the recipient's exact email ID.
- dont assume recipients email id on the basis of the information entered by the user, explicity ask the email to which this message has to be sent
- Do **not** send the email until a valid email ID has been provided.
- important: the email has to be well structured like it was in the template, with proper paragraphs, dont just combine all the info into one paragraph into one and send it. also in the sent email in can see newline characters, this is send through api, so make sure that the send email, doesnt have these charcters and is complete i.e exactly what user selected
- think again if you have followed the above instruction in step 7, if not correct them.
- Upon receiving a valid email, send the final formatted email.

# Step 8: congratulate the user
- After successfully sending the email, congratulate the user

# Step 9: Repeat Process
- Offer the user the option to repeat the process for additional profiles or recipients.
"""

StartMsg = "HEY THERE!😊"


st.set_page_config(
        page_title= "EmailGenie",
        page_icon= "🧞‍♂️")

ipAddress = st.context.headers.get("x-forwarded-for")


def __nowInIST() -> DT.datetime:
    return DT.datetime.now(pytz.timezone("Asia/Kolkata"))


def pprint(log: str):
    now = __nowInIST()
    now = now.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] [{ipAddress}] {log}")


pprint("\n")

st.markdown(
    """
    <style>
    @keyframes blinker {
        0% {
            opacity: 1;
        }
        50% {
            opacity: 0.2;
        }
        100% {
            opacity: 1;
        }
    }
    .blinking {
        animation: blinker 3s ease-out infinite;
    }
    .code {
        color: green;
        border-radius: 3px;
        padding: 2px 4px; /* Padding around the text */
        font-family: 'Courier New', Courier, monospace; /* Monospace font */
    }
    div[aria-label="dialog"] {
        width: 90vw;
    }
    </style>
    """,
    unsafe_allow_html=True
)


def isInvalidResponse(response: str):
    # new line followed by small case char
    if len(re.findall(r'\n[a-z]', response)) > 3:
        return True

    # lot of repeating words
    if len(re.findall(r'\b(\w+)(\s+\1){2,}\b', response)) > 1:
        return True

    # lots of paragraphs
    if len(re.findall(r'\n\n', response)) > 25:
        return True

def resetButtonState():
    st.session_state["buttonValue"] = ""


def setStartMsg(msg):
    st.session_state.startMsg = msg


if "chatHistory" not in st.session_state:
    st.session_state.chatHistory = []

if "messages" not in st.session_state:
    st.session_state.messages = []

if "buttonValue" not in st.session_state:
    resetButtonState()

if "startMsg" not in st.session_state:
    st.session_state.startMsg = ""

if "emailSent" not in st.session_state:
    st.session_state.emailSent = False

st.session_state.toolResponseDisplay = {}


def getMessages():
    def getContextSize():
        currContextSize = countTokens(SYSTEM_MSG) + countTokens(st.session_state.messages) + 150
        pprint(f"{currContextSize=}")
        return currContextSize

    while getContextSize() > maxTokens:
        pprint("Context size exceeded, removing first message")
        st.session_state.messages.pop(0)

    return st.session_state.messages

tools = [
    toolsInfo["customerDetailsGsheets"]["schema"],
    toolsInfo["saveTemplate"]["schema"],
    toolsInfo["sendEmail"]["schema"],
]

def showToolResponse(toolResponseDisplay : dict):
    # Directly display the message without any icon
    st.markdown(toolResponseDisplay.get("text"))

def addToolCallToMsgs(toolCall: dict):
    st.session_state.messages.append(
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": toolCall.id,
                    "function": {
                        "name": toolCall.function.name,
                        "arguments": toolCall.function.arguments,
                    },
                    "type": toolCall.type,
                }
            ],
        }
    )

def processToolCalls(toolCalls):
    for toolCall in toolCalls:
        functionName = toolCall.function.name
        functionToCall = toolsInfo[functionName]["func"]
        functionArgsStr = toolCall.function.arguments
        pprint(f"{functionName=} | {functionArgsStr=}")
        functionArgs = json.loads(functionArgsStr)
        functionResult = functionToCall(**functionArgs)
        functionResponse = functionResult.get("response")
        responseDisplay = functionResult.get("display")
        pprint(f"{functionResponse=}")

        if responseDisplay:
            showToolResponse(responseDisplay)
            st.session_state.toolResponseDisplay = responseDisplay

        addToolCallToMsgs(toolCall)
        st.session_state.messages.append(
            {
                "role": "tool",
                "tool_call_id": toolCall.id,
                "name": functionName,
                "content": functionResponse,
            }
        )


def dedupeToolCalls(toolCalls: list):
    toolCallsDict = {}
    for toolCall in toolCalls:
        toolCallsDict[toolCall.function.name] = toolCall
    dedupedToolCalls = list(toolCallsDict.values())

    if len(toolCalls) != len(dedupedToolCalls):
        pprint("Deduped tool calls!")
        pprint(f"{toolCalls=} -> {dedupedToolCalls=}")

    return dedupedToolCalls


def getRandomToolId():
    return ''.join(
        random.choices(
            string.ascii_lowercase + string.digits,
            k=4
        )
    )

def predict(model: str = None):
    MODEL = model or model_def

    messagesFormatted = [{"role": "system", "content": SYSTEM_MSG}]
    messagesFormatted.extend(getMessages())
    contextSize = countTokens(messagesFormatted)
    pprint(f"{contextSize=} | {MODEL}")
    pprint(f"{messagesFormatted=}")

    response = client.chat.completions.create(
        model=MODEL,
        messages=messagesFormatted,
        temperature=0.5,
        max_tokens=4000,
        stream=False,
        tools=tools
    )

    responseMessage = response.choices[0].message
    # pprint(f"{responseMessage=}")
    responseContent = responseMessage.content
    # pprint(f"{responseContent=}")

    if responseContent and '<function=' in responseContent:
        pprint("Switching to TOOLS_MODEL")
        return predict(toolsModel)


    if responseContent:
        yield responseContent
    toolCalls = responseMessage.tool_calls
    # pprint(f"{toolCalls=}")

    if toolCalls:
        pprint(f"{toolCalls=}")
        toolCalls = dedupeToolCalls(toolCalls)
        try:
            processToolCalls(toolCalls)
            return predict()
        except Exception as e:
            pprint(e)

st.title("EmailGenie 📧🧞‍♂️")
if not (st.session_state["buttonValue"] or st.session_state["startMsg"]):
    st.button(StartMsg, on_click=lambda: setStartMsg(StartMsg))
for chat in st.session_state.chatHistory:
    role = chat["role"]
    content = chat["content"]
    toolResponseDisplay = chat.get("toolResponseDisplay")
    with st.chat_message(role):
        st.markdown(content)
        if toolResponseDisplay:
           showToolResponse(toolResponseDisplay)

         
if prompt := (st.chat_input() or st.session_state["buttonValue"] or st.session_state["startMsg"]):
    resetButtonState()
    setStartMsg("")

    with st.chat_message("user"):
        st.markdown(prompt)
    pprint(f"{prompt=}")
    st.session_state.chatHistory.append({"role": "user", "content": prompt })
    st.session_state.messages.append({"role": "user", "content": prompt })

    with st.chat_message("assistant"):
        responseContainer = st.empty()

        def __printAndGetResponse():
            response = ""
            # responseContainer.markdown(".....")
            responseGenerator = predict()

            for chunk in responseGenerator:
                response += chunk
                if isInvalidResponse(response):
                    pprint(f"Invalid_{response=}")
                    return
                responseContainer.markdown(response)

            return response

        response = __printAndGetResponse()
        while not response:
            pprint("Empty response. Retrying..")
            time.sleep(0.5)
            response = __printAndGetResponse()

        pprint(f"{response=}")

        def selectButton(optionLabel):
            st.session_state["buttonValue"] = optionLabel
            pprint(f"Selected: {optionLabel}")

        toolResponseDisplay = st.session_state.toolResponseDisplay
        st.session_state.chatHistory.append({
            "role": "assistant",
            "content": response,
            "toolResponseDisplay": toolResponseDisplay
        })

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
        })