from flask import Flask,jsonify,request
import os
import openai
from dotenv import load_dotenv
import requests
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import uuid
from bson.json_util import dumps


app = Flask(__name__)
CORS(app)
load_dotenv()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

MONGO_URL = os.environ.get("MONGO_URL")

client = MongoClient(MONGO_URL)
db = client['cosmos-Flask']
user_collection = db["users"]
chat_collection = db["chats"]

def serialize_doc(doc):
    doc['_id'] = str(doc['_id'])
    doc["chatid"] = str(doc["chatid"])
    doc["user_id"] = str(doc["user_id"])
    return doc

def serialize_user(doc):
    print(doc)
    doc['_id'] = str(doc['_id'])
    return doc

def query_builder(query):
    # System message with an example to set the context and instruct the model
    prompt = """[Take a role of query builder], user will ask questions related to parenting and children. your task is to analyse query and ask 2 follow up (should not have sub questions) questions one by one to users. After 3 followup questions you should include all answers from user to build better prompt for gpt model which answers user questions, to identify prompt you can use special characters like #. you can ask age of child and situations
    Example : user : 'My son bites when he is angry'
    Assisant : 'How old is your son?'
    user : '6 years'
    Assistant : 'Is this biting behavior a recent development or has your son been biting when angry for a while now?'
    user : 'yes'
    Assistant : 'Have you noticed any specific triggers or patterns that lead to your son feeling angry and resorting to biting?'
    user : 'angry'
    Assistant : 'Prompt : My son bites when he is angry. He is 6 years old and has been exhibiting this behavior for a while now. There are no specific triggers or patterns that lead to his anger. No strategies or techniques have been implemented to help him manage his anger and prevent biting.'
    """
    
    # Prepare messages for the API call
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": query}
    ]

    # API endpoint URL
    api_url = "https://api.openai.com/v1/chat/completions"

    # API request headers
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",  # Replace OPENAI_API_KEY with your actual API key
        "Content-Type": "application/json"
    }

    # API request payload
    payload = {
        "model": "gpt-3.5-turbo-16k",
        "messages": messages,
        "temperature": 1.21,
        "max_tokens": 255,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    # Make the POST request to the OpenAI API
    response = requests.post(api_url, json=payload, headers=headers)

    # Extract the response from the API call
    response_data = response.json()
    response_text = response_data['choices'][0]['message']['content']
    return response_text

def get_response(query):
     # System message with an example to set the context and instruct the model
    prompt = f"""You are a social media influencer with a focus on parenting and children. Your role is to provide thoughtful and engaging responses to questions asked by your followers. The information you share should be accurate, non-technical, and research-based, delivered in a heart-to-heart manner. Your responses should match the tone and style of an influencer, providing contextually relevant answers that resonate with your audience.

    To enhance your responses, you can incorporate examples and personal anecdotes to illustrate your points. When clarifying questions arise, feel free to ask 2-3 follow-up questions for better clarity, allowing you to tailor your answers to each individual's needs.

    Remember that your responses should be presented in paragraph form, avoiding bullet or numbered points, and refraining from using headings. This format will create a more engaging and seamless reading experience for your audience.

    Example: User - user : 'I have two daughters. One is 8 years and other is 3.5 years old.
    Elder one is little becoming inferior. She afraid of to asking questions. She is afraid that she will be scolded if she asks questions. That’s why she doesn’t ask questions. Whether it’s studies or other things. We are also at mistake as parents. What should I do? She can’t talk to anyone without fear. '
    Assistant : 'You can try 3 things:
    1. Asking child why she is not asking questions? She could say that she did ask in the school but teacher scolded back. Whatever she says, you may listen. It is possible that she says no because she is scared. 
    2. Then you may say her that you can ask any question to mommy. Mom will not scold her. Even if you did in the past, it will not repeat. This way, your daughter will have one person to whom she can ask questions. 
    3. Check the school once whether they allow students to ask questions or not.'
    user : 'My daughter is 19 mnths. But jab usko me koi chij nai deti hu ya uski koi zid Puri nai kti hu tou wo mujhe hit karti haiShe is just 19 mnths..how can I control this behaviourYa kabhi kabhi wo masti me b mujhe hit kar deti hai.

    I tell her hitting noo..nd wo khud b bolti hai hitting nooo..but not regularly..but spcly wen i don't listen to her'
    Assistsnt: 'Meherr ji - sorry for the late reply. Aapki beti choti hai. Is umar mein kuch na milne pe kaise behave karna hai bachon ko pata nahin hota. Emotion pe kaabu nahin hota. Lekin bachon ka bhi maarna rok sakte hai. Thoda time laga ke.
    Kabhi bhi jiss cheez ke liye bacha hit kar raha hai woh puri nahin karni kyonki phir bachey ko lagta hai ke maarne se cheez milegi. So a no means a no. But pyaar se.
    Aap calm aawaaz mein usko bol sakti hai - No using hands and feet. Mujhe lagti hai. Same line hi humein baar baar use karni hai.
    Phir Aap uski feeling ko acknowledge karo. Ke aapko woh chahiye. Haan? Mujhe pata hai. Mujhe pata hai aapko aacha lagta hai. Lekin maarne se kabhi nahin milega. Mummy loves you. 
    Bachon ke nervous system ko touch karne se calmnes milti hai. Unko touch karke pyaar se mana karenge to baat samajne ka chance zyada hai.
    Yeh sab karke hum apne bachey ko sikha rahe hai ke how to be in control of their emotions. Yeh imp learning sabse pehle maa baap se hi aati hai :-)
    Lots of love to your family <heart symbol>'
    user:'Harpreet jiMeri 10 saal ki beti hai jab bhi humare sath khelti h aur usse chaut lg jati h to wo roti nhi h agar usse pain hota h to bhi bs bolti h dard nhi ho rha h apne emotions nhi dhikhati h agar Rona aa rha hota h to bhi control kr leti h...kya ye normal h ya koi aur wajah h plss help me in this.

    Dukhi hoti h to ek do baar puchne pr bta deti h lekin jb usse Rona aata h kisi bhi baat pr to roti nhi h aur dba leti h apne emotion ko mujhe lgta h ki wo dukhi h bt wo khti h thik hu main kuch nhi hua

    Kyuki jb main baar baar puchti Hu ki kuch hua h kya to btati h ki dadu ne daanta ya dadi ne .. otherwise main aur husband ke beech kabhi argument ho jata h to wo hamesha rone lgti h aur mujhe khti h mumma plss aap chup ho jao...aap Mt boloLikeForwardCopyReportMere in laws ke beech kafi arguments hote h .. to wo apni dadi se khti h ki dadi aap chup ho jao aur rone lgti h....usko kabhi chot LG jati h to mere samne to bolti h ki dard ho rha h lekin husband ke samne bolti h kuch nhi hua..ya mumma papa ko Mt bolna wo ..ye soch kr ki hum dono k beech bhi argument ho jayega

    Main isko kaise thik kru??'
    Assitant:'Rajpriya ji, yeh sirf aap chot lagne par bol rahi hai ya in general bhi agar dukhi lag rahi hai to baat nahin kartiLikeForwardCopyUnsendPlease do share more

    Aapko kyon lagta hai ke aapki beti dukhi hai?

    Rajpriya ji, the environment in your house is impacting your child. Ghar ke badao ke karan bache parr asar pad gaya haiAgar bade landenge ya bachey ko alag alag cheez bolenge ya daantenge to bacha apni feelings dabana shuru ho jayegaLikeForwardCopyUnsendHuman's ke dimaag ka ek simple udeshya hai - bachey ko safe feel karwana

    Agar usko safe feel nahin hota, calm nahin feel hota, to woh dheere develop hota hai. Sochiye ke aap pareshaan hai. Jabb hum pareshaan hote hai to kaam pe focus nahin kar paate aur dukhi rehte haiwahi apki beti ke saath ho sakta haihttps://www.instagram.com/p/Co7CvllIXwy/Joint family mein agar bade sab same page pe ho, to bachey ke liye best haiLikeForwardCopyUnsendAap do teen cheezein kar sakti hai- apni beti ke saath bahar walks pe ja sakti hai, taaki aap dono ko akele aacha simple time mile- aapke husband bhi yeh kar sakte hai uske saath- aap apna relationship apne husband aur inlaws ke saath improve kar sakti hai taaki ghar mein ladayi nahin ho. Unko bata sakti hai ke yeh hamare bachey ke liye zaroori hai
    user : 'My 3 yr old kind of feeling that his younger brother is getting all the attention. He keeps on beating or pushing the younger one tries all the ways to hurt the younger brother. When elder left alone with younger one then he will just keeps on beating with whatever he got. But sometimes he cares for him. I don't know what to do. He doesn't want me to breastfeed feed the younger baby. And he wants me to breastfeed feed him and he only want to be with me. But iam unable to give him time because he wants me only when the younger one needs me for breastfeeding please suggest something sir'
    Assistant: 'Priyanka - when the younger child comes we forget the older childYour older child only needs to know his quota of love from you is secureSo you can catch him, hold him and tell him I love you.And you can say see everyday we will spend time togetherand you can spend 15-30 min with him without your younger childthe elder one needs love coz he is missing itthat's allLikeForwardCopyUnsendand you can also involve him in saying listen we are a family. all of us together.'
    user: 'Dear Harpreeth, We have a toddler (daughter) who is aged 2.9 Yrs undergoing a rough phase. The issue is that,
    1. We had a nanny - 21 Yrs (Rohini) with whom our daughter enjoyed a lot, playing, signing, dancing etc. The nanny (Rohini) was also good and she played with her nicely
    2. Unfortunately, she ended up leaving because of her personal problems & there was no clear closure for my daughter. The nanny was a live-in nanny.
    3. Even today my daughter recalls the songs that they sang together, cherishes the games they played and remembers her at-least 6-7 times a day
    4. We have replaced her with a nanny, who is much more good but aged around 35 Yrs. But this nanny is a day nanny, comes at 10 and leaves at 7. Its more than 1.5 months and my daughter has not adjusted to the new nanny. She gets irritated and reluctant to play or move with her. She has become clingy to me and my wife.
    5. I am clueless, what to do? Can you please help us out.
    In case, if you can be reached out through phone and provide a consultancy that would be great. Will wait for your reply.'"""
    # Prepare messages for the API call
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": query}
    ]

    # API endpoint URL
    api_url = "https://api.openai.com/v1/chat/completions"

    # API request headers
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # API request payload
    payload = {
        "model" : "gpt-3.5-turbo-16k",
        "messages": messages,
        "temperature": 1.21,
        "max_tokens": 255,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }

    # Make the POST request to the OpenAI API
    response = requests.post(api_url, json=payload, headers=headers)

    # Extract the response from the API call
    response_data = response.json()
    response_text = response_data['choices'][0]['message']['content']
    return response_text
    

@app.route("/query",methods = ["POST"])
def post_query():
    data = request.get_json()
    query = data["query"]
    response = query_builder(query)
    return jsonify({"msg" : {"query" : query,"response" : response}})

@app.route("/register",methods=["POST"])
def post_user():
    new_registration = request.get_json()
    print(new_registration)
    find_user = user_collection.find_one({"email" : new_registration["email"]})
    if find_user is not None:
        return jsonify({"msg" : "User is already present!!"}),400
    else:
        result = user_collection.insert_one(new_registration)
        
        # Convert the inserted document's ObjectId to a string representation
        new_registration['_id'] = str(result.inserted_id)

        return jsonify({"msg": "New User Registered!!", "User": new_registration})



@app.route("/login",methods=["POST"])
def login_user():
    user_login = request.get_json()
    print(user_login)
    find_user = user_collection.find_one({"email" : user_login["email"]})
    print(find_user)
    serialized_user = serialize_user(find_user)
    if find_user is not None:
        if find_user["password"] == user_login["password"]:
            return jsonify({"msg":"Login Successful!!","user" : serialized_user})
        else:
            return jsonify({"msg": "Password is Wrong!!"}),400
    else: 
        return jsonify({"msg" : "User not found. Please register!!"}),400
    


@app.route("/add_chat",methods = ["POST"])
def add_new_chat():
    request_data = request.get_json()
    print(request_data);
    new_chat = {
        "chatid" :  str(uuid.uuid4()),
        "chat_name" : request_data["name"],
        "chat_history" : [],
        "user_id" : request_data["_id"]
    }
    chat_collection.insert_one(new_chat)
    return jsonify({"msg" : "New chat has been added"})

def serialize_docs(docs):
    serialized_docs = []
    for doc in docs:
        doc['_id'] = str(doc['_id'])
        doc["chatid"] = str(doc["chatid"])
        doc["user_id"] = str(doc["user_id"])
        serialized_docs.append(doc)
    return serialized_docs

@app.route("/get_chat/<user_id>", methods=["GET"])
def get_chat(user_id):
     # Find all chat documents with the given user_id
    chats = chat_collection.find({"user_id": user_id})

    serialized_users = serialize_docs(chats)

   
    return jsonify({"chats": serialized_users})



@app.route("/get_single_chat/<chatid>", methods=["GET"])
def get_single_chat(chatid):
    chat = chat_collection.find_one({"chatid": chatid})
    print(chat, chatid)
    if chat:
        serialized_chat = serialize_doc(chat)
        return jsonify({"chat": serialized_chat})
    else:
        return jsonify({"message": "Chat not found"})
    
@app.route("/query/<chatid>", methods=["POST"])
def post_query_chat(chatid):
    data = request.get_json()
    print(data)
    query = data["query"]
    response = get_response(query)

    # Create query and response documents
    query_doc = {"type": "query", "msg": query}
    response_doc = {"type": "response", "msg": response}

    # Push the documents to the chat's chathistory array
    chat_collection.update_one(
        {"chatid": chatid},
        {"$push": {"chat_history": {"$each": [query_doc, response_doc]}}}
    )
    chat = chat_collection.find_one({"chatid": chatid})
    serialized_chat = serialize_doc(chat)

    return jsonify({"chat": serialized_chat})
   

if __name__ == "__main__":
    app.run()