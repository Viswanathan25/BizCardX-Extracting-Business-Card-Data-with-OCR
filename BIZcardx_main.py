import pandas as pd
import easyocr
import streamlit as st
import psycopg2
from streamlit_option_menu import option_menu
import matplotlib.pyplot as plt
import os
import cv2
import re

# SETTING PAGE CONFIGURATIONS
st.set_page_config(layout="wide")

with st.sidebar:
    selected = option_menu(
        menu_title = "BIZcards_project",
        options = ["Intro","Upload & Extract","Modify"],
        icons=["house","cloud-upload","pencil-square"],
        default_index=0,
        styles = {"nav-link": {"font-size": "20px", "text-align": "centre", "margin": "0px", "--hover-color": "#6495ED"},
                   "icon": {"font-size": "20px"},
                   "container": {"max-width": "300px"},
                   "nav-link-selected": {"background-color": "#6495ED"}})
# INITIALIZING THE EasyOCR READER
reader = easyocr.Reader(['en'])

#connecting sql
project = psycopg2.connect(host='localhost', user='postgres', password='Enter_your_password', database='create_db')
cursor = project.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS card_details
                   (card_holder TEXT,
                    company_name TEXT,
                    designation TEXT,
                    mobile_number VARCHAR(20) PRIMARY KEY,
                    email TEXT,
                    website TEXT,
                    area TEXT,
                    city TEXT,
                    state TEXT,
                    pin_code VARCHAR(10)
                    )''')
project.commit()

#HOME MENU
if selected == "Intro":
    col1,col2 = st.columns(2)
    with col1:
        st.header(":violet[*BizCardX: Extracting Business Card Data with OCR*] by Viswanathan")
        st.markdown(":violet[*Technologies Used :*] Python,easy OCR, Streamlit, SQL, Pandas")
        st.markdown(":violet[*Overview :*] In this streamlit web app you can upload an image of a business card and extract relevant information from it using easyOCR. You can view, modify or delete the extracted data in this app. This app would also allow users to save the extracted information into a database along with the uploaded business card image. The database would be able to store multiple entries, each with its own business card image and extracted information.")

    with col2:
        st.image("https://user-images.githubusercontent.com/117557948/241384159-85e6a6ee-d508-4d35-8124-85b6613e76a7.gif")
        st.image("sam1.jpg")
if selected == "Upload & Extract":
    st.markdown("### Upload a Business Card")
    uploaded_card = st.file_uploader("upload here",label_visibility="collapsed",type=["png","jpeg","jpg"])

    if uploaded_card is not None:
        uploaded_cards_dir = os.path.join(os.getcwd(), "uploaded_cards")
        os.makedirs(uploaded_cards_dir, exist_ok=True)  # Create the directory if it doesn't exist
        with open(os.path.join(uploaded_cards_dir, uploaded_card.name), "wb") as f:
            f.write(uploaded_card.getbuffer())

        def image_preview(image,res):
            for (bbox, text, prob) in res:
                (tl, tr, br, bl) = bbox
                tl = (int(tl[0]),int(tl[1]))
                tr = (int(tr[0]),int(tr[1]))
                br = (int(br[0]),int(br[1]))
                bl = (int(bl[0]),int(bl[1]))
                cv2.rectangle(image, tl, br, (0, 255, 0), 2)
                cv2.putText(image, text, (tl[0], tl[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            plt.rcParams['figure.figsize'] = (15, 15)
            plt.axis('off')
            plt.imshow(image)

        #DISPLAYING CARDS
        col1,col2 = st.columns(2,gap="large")
        with col1:
            st.markdown("#     ")
            st.markdown("#     ")
            st.markdown("### You Have Uploaded the card")
            st.image(uploaded_card)
        with col2:
            st.markdown("#     ")
            st.markdown("#     ")
            with st.spinner("processing image please wait"):
                st.set_option('deprecation.showPyplotGlobalUse', False)
                saved_img = os.getcwd() + "\\" + "uploaded_cards" + "\\" + uploaded_card.name
                image = cv2.imread(saved_img)
                res = reader.readtext(saved_img)
                st.markdown("### Image Processed and Data Extracted")
                st.pyplot(image_preview(image, res))

        saved_img = os.getcwd() + "\\" + "uploaded_cards" + "\\" + uploaded_card.name
        result = reader.readtext(saved_img, detail=0, paragraph=False)

        #CONVERTING IMG TO BINARY TO UPLOAD SQL
        def img_to_binary(file):
            with open(file, "rb") as file:
                binaryData = file.read()
            return binaryData

        data = {"card_holder" : [],
                "company_name" : [],
                "designation" : [],
                "mobile_number" : [],
                "email" : [],
                "website" : [],
                "area" : [],
                "city" : [],
                "state" : [],
                "pin_code" : [],
              #  "image" : img_to_binary(saved_img)
                }

        def get_data(res):
            for ind, i in enumerate(res):

                # To get WEBSITE_URL
                if "www " in i.lower() or "www." in i.lower():
                    data["website"].append(i)
                elif "WWW" in i:
                    data["website"] = res[4] + "." + res[5]

                #To get mail id
                elif "@" in i:
                    data["email"].append(i)

                #T0 get Mob_ num
                elif "-" in i:
                    data["mobile_number"].append(i)
                    if len(data["mobile_number"]) == 2:
                        data["mobile_number"] = " & ".join(data["mobile_number"])

                #To get company_name
                elif ind == len(res) - 1:
                    data["company_name"].append(i)

                # To get CARD HOLDER NAME
                elif ind == 0:
                    data["card_holder"].append(i)

                # To get DESIGNATION
                elif ind == 1:
                    data["designation"].append(i)

                # To get AREA
                if re.findall('^[0-9].+, [a-zA-Z]+', i):
                    data["area"].append(i.split(',')[0])
                elif re.findall('[0-9] [a-zA-Z]+', i):
                    data["area"].append(i)

                # To get CITY NAME
                match1 = re.findall('.+St , ([a-zA-Z]+).+', i)
                match2 = re.findall('.+St,, ([a-zA-Z]+).+', i)
                match3 = re.findall('^[E].*', i)
                if match1:
                    data["city"].append(match1[0])
                elif match2:
                    data["city"].append(match2[0])
                elif match3:
                    data["city"].append(match3[0])

                # To get STATE
                state_match = re.findall('[a-zA-Z]{9} +[0-9]', i)
                if state_match:
                    data["state"].append(i[:9])
                elif re.findall('^[0-9].+, ([a-zA-Z]+);', i):
                    data["state"].append(i.split()[-1])
                if len(data["state"]) == 2:
                    data["state"].pop(0)

                # To get PINCODE
                if len(i) >= 6 and i.isdigit():
                    data["pin_code"].append(i)
                elif re.findall('[a-zA-Z]{9} +[0-9]', i):
                    data["pin_code"].append(i[10:])
        get_data(result)

        #fuction create df
        def create_df(data):
            df = pd.DataFrame(data)
            return df
        df = create_df(data)
        st.success("### Data Extracted")
        st.write(df)

        if st.button("## Upload To Database"):
            for i,row in df.iterrows():
                sql = """
                    INSERT INTO card_details (card_holder,company_name,designation, 
                    mobile_number,email,website,area,city,state,pin_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                cursor.execute(sql,tuple(row))
                project.commit()
            st.success("#### Uploaded to database successfully!")

# MODIFY MENU

# MODIFY MENU
if selected == "Modify":
    col1, col2, col3 = st.columns([3, 3, 2])
    col2.markdown("## Alter or Delete the data here")
    column1, column2 = st.columns(2, gap="large")
    try:
        with column1:
            cursor.execute("SELECT card_holder FROM card_details")
            result = cursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to update", list(business_cards.keys()))
            st.markdown("#### Update or modify any data below")
            cursor.execute("select card_holder,company_name,designation,mobile_number,"
                           "email,website,area,city,state,pin_code from card_details WHERE card_holder=%s",
                            (selected_card,))
            result = cursor.fetchone()

            # DISPLAYING ALL THE INFORMATIONS
            card_holder = st.text_input("Card_Holder", result[0])
            company_name = st.text_input("Company_Name", result[1])
            designation = st.text_input("Designation", result[2])
            mobile_number = st.text_input("Mobile_Number", result[3])
            email = st.text_input("Email", result[4])
            website = st.text_input("Website", result[5])
            area = st.text_input("Area", result[6])
            city = st.text_input("City", result[7])
            state = st.text_input("State", result[8])
            pin_code = st.text_input("Pin_Code", result[9])

            if st.button("Commit changes to DB"):
                # Update the information for the selected business card in the database
                cursor.execute("""UPDATE card_details SET card_holder=%s,company_name=%s,designation=%s,mobile_number=%s,
                               email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                WHERE card_holder=%s""",(card_holder, company_name, designation, mobile_number, email, website, area, city, state, pin_code,
                                selected_card))
                project.commit()
                st.success("Information updated in database successfully.")

        with column2:
            cursor.execute("SELECT card_holder FROM card_details")
            result = cursor.fetchall()
            business_cards = {}
            for row in result:
                business_cards[row[0]] = row[0]
            selected_card = st.selectbox("Select a card holder name to Delete", list(business_cards.keys()))
            st.write(f"### You have selected :green[**{selected_card}'s**] card to delete")
            st.write("#### Proceed to delete this card?")

            if st.button("Yes Delete Business Card"):
                cursor.execute(f"DELETE FROM card_details WHERE card_holder='{selected_card}'")
                project.commit()
                st.success("Business card information deleted from database.")
    except:
        st.warning("There is no data available in the database")

    if st.button("View updated data"):
        cursor.execute("select card_holder,company_name,designation,mobile_number,email,website,area,city,state,pin_code from card_details")
        updated_df = pd.DataFrame(cursor.fetchall(),
                                  columns=["Card_Holder", "Company_Name", "Designation", "Mobile_Number", "Email",
                                           "Website", "Area", "City", "State", "Pin_Code"])
        st.write(updated_df)

















