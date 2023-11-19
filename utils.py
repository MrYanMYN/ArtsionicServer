import time
from datetime import date
import json

import mysql.connector
from rembg import remove
from io import BytesIO
from super_image import EdsrModel, ImageLoader
from PIL import Image
import openai
import base64
import os
import requests
from pytrends.request import TrendReq
import pandas as pd
import logging
from dalle3 import Dalle
import sqlite3
import printify as ptfy
from dotenv import load_dotenv
from removebg import RemoveBg
# API Values

load_dotenv()

openai.api_key = os.environ.get('OPENAI_API_KEY')
dreamstudio_api_key = os.environ.get('DREAMSTUDIO_API_KEY')
dalle3_cookie = os.environ.get('DALLE3_COOKIE')
API_KEY_PRINTIFY = os.environ.get('PRINTIFY_API_KEY')

def autolog(func):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        log_msg = f"Called {func.__name__}({args}, {kwargs}) => {result}"
        # Truncate the log message to 150 characters if it's longer
        if len(log_msg) > 250:
            log_msg = log_msg[:247] + "..."
        logger.info(log_msg)
        return result
    return wrapper

@autolog
def extended_trends_pull(region):
    pytrend = TrendReq()
    df = pytrend.trending_searches(pn=region)
    trends = {}
    tmp_df = df

    for i in range(0, 19):
        # trends.append(df.at[i, 0])
        currentTrend = df.at[i, 0]
        while True:
            try:
                topics = pytrend.suggestions(keyword=currentTrend)
                filtered_topics = [{'title': topic['title'], 'type': topic['type']} for topic in topics]
                trends[i] = {"trend": df.at[i, 0], "news": "", "relatedTopics": filtered_topics}
                break

            except:
                pass

        df = tmp_df

    return trends
@autolog
def pull_trends(region):
    pytrend = TrendReq()
    df = pytrend.trending_searches(pn=region)
    trends = {}
    tmp_df = df

    for i in range(0, 19):
        # trends.append(df.at[i, 0])
        currentTrend = df.at[i, 0]
        while True:
            try:
                # topics = pytrend.suggestions(keyword=currentTrend)
                # filtered_topics = [{'title': topic['title'], 'type': topic['type']} for topic in topics]
                filtered_topics = []
                trends[i] = {"trend": df.at[i, 0], "news": "", "relatedTopics": filtered_topics}
                break

            except:
                pass

        df = tmp_df

    return trends

@autolog
def filter_trends(trends):
    keywords = []
    pytrend = TrendReq()
    for i in range(0, len(trends)):
        keyword = pytrend.suggestions(keyword=trends[i])
        df = pd.DataFrame(keyword)
        keyword = df.to_dict()
        keywords.append(keyword)

    good_words = ["Film", "Book", "Game", "musician", "band", "Television", "series", "artist", "Song", "Musical","Sports",
                  "Art", "Paint", "Painter", "War", "Invasion", "Invade", "President", "Event", "Historical", "History"]
    drawble_trends = []

    for item in range(len(keywords)):

        try:
            for i in range(len(keywords[item]["type"])):
                for word in good_words:
                    if word.upper() in keywords[item]["type"][i].upper():
                        drawble_trends.append(keywords[item]["title"][0])
                        break
                break
        except:
            pass

    return drawble_trends

@autolog
def generate_prompt(trend):
    # openai.api_base = "http://localhost:1234/v1"
    # systemPrompt = f"""
    #         You are an amazing prompt engenieer that is here to design prompts for a text-to-image AI and to preserve the luminous / neon / radiant one color theme. Created prompts from topics like the following examples:
    #
    #         Star Wars - Illustration of a luminous yellow BB-8 droid with vibrant energy patterns circling its spherical body, showcased on a pitch-black background.
    #         Hottest pepper in the world - Illustration of a radiant green chili pepper, denoting the world's most fiery, with sizzling energy ripples flowing from its base, displayed on a dark black canvas.
    #         Justin Timberlake - Illustration of a luminous purple vinyl record with vibrant sound waves undulating from its center, placed on a pitch-black background.
    #         Music - Illustration of a stylized vinyl record with dynamic neon blue sound waves emanating from its center against a dark black background.
    #         Star Wars - Illustration of a luminous red Death Star with vibrant energy beams radiating from its core, placed on a pitch-black background.
    #         Mexico Vs Germany - Illustration of a luminous blue football boot, representing the athletic prowess in the Mexico vs Germany game, with vibrant sound waves flowing out, placed against a pitch-black backdrop.
    #         Taylor Swift - Illustration of a neon green treble clef surrounded by swirling electric sound waves, contrasting against a deep black backdrop.
    #         Diablo 4 Season 2 - Illustration of an illuminated green demonic sigil inspired by Diablo_4 Season_2 radiating with malevolent energy on a stark black canvas
    #     """

    systemPrompt = """
    You are an amazing prompt engenieer that is here to design prompts for a text-to-image AI and to preserve the luminous / neon / radiant one color theme. Created prompts from topics guidede by the following guidelines:
    Art Style: luminous, Neon, vibrant, radiant illustration
    Font Style for Logos: Dynamic, urban graffiti-style font with a subtle integration of the frog king silhouette within the letters.
    Color Palette: Vivid and eye-catching, suitable for T-shirt merchandise.
    Background: None, to highlight the design on merchandise.x
    Brand: If given a brand / company name, keey it in the generated prompt.
    
    Examples:
           
    Star Wars - Illustration of a luminous yellow BB-8 droid with vibrant energy patterns circling its spherical body, showcased on a pitch-black background.
    Hottest pepper in the world - Illustration of a radiant green chili pepper, denoting the world's most fiery, with sizzling energy ripples flowing from its base, displayed on a dark black canvas.
    Justin Timberlake - Illustration of a luminous purple vinyl record with vibrant sound waves undulating from its center, placed on a pitch-black background.
    Music - Illustration of a stylized vinyl record with dynamic neon blue sound waves emanating from its center against a dark black background.
    Star Wars - Illustration of a luminous red Death Star with vibrant energy beams radiating from its core, placed on a pitch-black background.
    Mexico Vs Germany - Illustration of a luminous blue football boot, representing the athletic prowess in the Mexico vs Germany game, with vibrant sound waves flowing out, placed against a pitch-black backdrop.
    Taylor Swift - Illustration of a neon green treble clef surrounded by swirling electric sound waves, contrasting against a deep black backdrop.
    Diablo 4 Season 2 - Illustration of an illuminated green demonic sigil inspired by Diablo_4 Season_2 radiating with malevolent energy on a stark black canvas
    """
    while True:
        try:
            pytrend = TrendReq()
            topics = pytrend.suggestions(keyword=trend)
            filtered_topics = [{'title': topic['title'], 'type': topic['type']} for topic in topics]
            break
        except:
            pass

    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": systemPrompt},
                  {"role": "user",
                   "content": f"I'll give you some context about the trend you'll be generating it will be related to the following topics: {filtered_topics}. Respond ONLY with the prompt. \n {trend} - "}],
    )

    output = response.dict()['choices'][0]['message']['content']
    return output

class ImageGen:
    def __init__(self, prompt, trend, db_name):
        load_dotenv()
        self.db_name = os.environ.get('DB_NAME')
        self.db_username = os.environ.get('DB_USER')
        self.db_password = os.environ.get('DB_PASS')
        self.db_host = os.environ.get('DB_HOST')
        self.db_port = int(os.environ.get('DB_PORT'))
        self.prompt = prompt
        self.trend = trend
        self.marketing_dict = {}

    @autolog
    def create_img(self):
        engine_id = "stable-diffusion-xl-1024-v1-0"
        api_host = os.getenv('API_HOST', 'https://api.stability.ai')
        if dreamstudio_api_key is None:
            raise Exception("Missing Stability API key.")

        response = requests.post(
            f"{api_host}/v1/generation/{engine_id}/text-to-image",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {dreamstudio_api_key}"
            },
            json={
                "text_prompts": [
                    {
                        "text": self.prompt
                    }
                ],
                "cfg_scale": 7,
                "height": 1024,
                "width": 1024,
                "samples": 1,
                "steps": 30,
            },
        )

        if response.status_code != 200:
            raise Exception("Non-200 response: " + str(response.text))

        data = response.json()
        image_path = f"./out/v1_txt2img_{self.trend}_{time.time()}.png"
        b64_img = ""
        for i, image in enumerate(data["artifacts"]):
            with open(image_path, "wb") as f:
                f.write(base64.b64decode(image["base64"]))
                b64_img = b64_img + image["base64"]

        return image_path, b64_img

    @autolog
    def create_img_dalle3_unoffical(self):
        try:
            logging.basicConfig(level=logging.INFO)
            dalle = Dalle(dalle3_cookie)
            dalle.create(self.prompt)
            urls = dalle.get_urls()
            dalle.download(urls, "images/")

        except Exception:
            self.create_img()

    def create_img_dalle3_offical(self):
        client = openai.OpenAI()

        response = client.images.generate(
            model="dall-e-3",
            prompt=self.prompt,
            size="1024x1024",
            quality="hd",
            n=1
        )

        image_url = response.data[0].url
        response = requests.get(image_url)
        image_path = f"./out/v1_txt2img_{self.trend}_{time.time()}.png"

        if response.status_code == 200:
            image_bytes = response.content
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            with open(image_path, 'wb') as file:
                file.write(response.content)
            return image_path, image_base64
        else:
            print(f'Failed to download image. Status code: {response.status_code}')

    @autolog
    def upscale_image(self, image_path):
        image = Image.open(image_path)

        model = EdsrModel.from_pretrained('eugenesiow/edsr-base', scale=2)
        inputs = ImageLoader.load_image(image)
        preds = model(inputs)

        upscaled_image_path = "temp/upscaled_2x.png"
        ImageLoader.save_image(preds, upscaled_image_path)
        ImageLoader.save_compare(inputs, preds, 'temp/scaled_2x_compare.png')
        return upscaled_image_path

    @autolog
    def upscale_img_via_api(self, image_path):
        engine_id = "esrgan-v1-x2plus"
        api_host = os.getenv('API_HOST', 'https://api.stability.ai')
        if dreamstudio_api_key is None:
            raise Exception("Missing Stability API key.")

        response = requests.post(
            f"{api_host}/v1/generation/{engine_id}/image-to-image/upscale",
            headers={
                "Accept": "image/png",
                "Authorization": f"Bearer {dreamstudio_api_key}"
            },
            files={
                "image": open(image_path, "rb")
            },
            data={
                "width": 2048,
            }
        )
        if response.status_code != 200:
            raise Exception("Non-200 response: " + str(response.text))

        upscaled_image_path = "temp/upscaled_2x.png"
        with open(upscaled_image_path, "wb") as f:
            f.write(response.content)

        return upscaled_image_path, response.content

    @autolog
    def remove_background(self, input_path, output_path):
        with open(input_path, 'rb') as f:
            image_data = f.read()

        output = remove(image_data)
        img = Image.open(BytesIO(output))
        img.save(output_path)

    @autolog
    def remove_background_via_api(self, input_path, output_path):
        """
        :param input_path: input path of the generated image
        :param output_path: output folder for saving
        :return: void, saves the img
        """
        rmbg = RemoveBg(os.environ.get("BG_REMOVER_API_KEY"), "error.log")
        with open(input_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        try:
            rmbg.remove_background_from_base64_img(encoded_string, new_file_name=output_path)
        except:
            print("Ran out of free BG remover quata!")



    @autolog
    def get_id(self, table_name, column_name, value):
        # Connect to the database
        conn = mysql.connector.connect(user=self.db_username, password=self.db_password, host=self.db_host, database=self.db_name, port=self.db_port)
        cursor = conn.cursor()

        # Execute the query
        cursor.execute(f"SELECT id FROM {table_name} WHERE {column_name}=%s", (value,))
        result = cursor.fetchone()

        # Close the connection
        conn.close()

        if result:
            return result[0]
        else:
            return None

    def update_basic_marketing_dict(self, data):
        self.marketing_dict['prompt'] = data['prompt']
        self.marketing_dict['trend'] = data['trend']
        self.marketing_dict['date'] = data['date']
        self.marketing_dict['imagePath'] = data['imagePath']

    @autolog
    def create_in_db_image(self):
        conn = mysql.connector.connect(user=self.db_username, password=self.db_password, host=self.db_host, database=self.db_name, port=self.db_port)
        cursor = conn.cursor()
        schema = """
                    CREATE TABLE IF NOT EXISTS products (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product TEXT,
                        description TEXT,
                        prompt TEXT,
                        trend TEXT,
                        hashtags TEXT,
                        date TEXT,
                        imagePath TEXT
                    );
                """

        cursor.execute(schema)
        # 5. Insert data into the table
        data = {
            'product': "",
            'description': "",
            'prompt': self.marketing_dict['prompt'],
            'trend': self.marketing_dict['trend'],
            'hashtags': "",
            'date': self.marketing_dict['date'],
            'imagePath': self.marketing_dict['imagePath']
        }

        # Use placeholders in the SQL query to insert data
        insert_query = """
                    INSERT INTO products (product, description, prompt, trend, hashtags, date, imagePath)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """

        # Check if a record with the same 'product' name already exists

        cursor.execute("SELECT id FROM products WHERE product = %s", (data['prompt'],))
        existing_record = cursor.fetchone()

        if existing_record is None:
            # Insert the data if no existing record is found
            cursor.execute(insert_query, (
            data['product'], data['description'], data['prompt'], data['trend'], data['hashtags'],
            data['date'], data['imagePath']))
            conn.commit()
            print("Data inserted successfully.")
        else:
            print("Data with the same product name already exists, no insertion performed.")

        conn.close()

    @autolog
    def generate_metadata(self):
        # openai.api_base = "http://localhost:1234/v1"
        systemPrompt = """
                    You are an amazing social media manager , generate instagram post content for each category a post Name , Description and hashtags. in json format and answer ONLY with the format. for example:
                    
                    Star Wars - {name: Beyond The Stars,Description: A depiction of the popular star wars franchise made by a popular fanartist,hashtags: #starwars #fanart #art #trending #lukas #disney #tshirts #printondemend}
                    Trevor Lawrence - {name: "The Rise of Trevor",Description: "A journey into the life and career of one of the most promising quarterbacks in the NFL", hashtags: "#trevorlawrence #jaguars #football #nfl #draft #qb #quarterback #lsu #tigers"}
                """
        pytrend = TrendReq()
        topics = pytrend.suggestions(keyword=self.trend)
        filtered_topics = [{'title': topic['title'], 'type': topic['type']} for topic in topics]

        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": systemPrompt},
                      {"role": "user",
                       "content": f"Topics related to the trend for background:{filtered_topics} \nGenerate content for: {self.trend} - "}],
        )

        to_parse = response.dict()['choices'][0]['message']['content']
        data_dict = json.loads(to_parse)
        current_date = date.today().strftime('%Y-%m-%d')
        data_dict['date'] = current_date

        self.marketing_dict = data_dict

        return data_dict

    @autolog
    def update_in_db_complete(self, metadata):
        conn = mysql.connector.connect(user=self.db_username, password=self.db_password, host=self.db_host, database=self.db_name, port=self.db_port)
        cursor = conn.cursor()
        schema = """
                    CREATE TABLE IF NOT EXISTS products (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product TEXT,
                        description TEXT,
                        prompt TEXT,
                        trend TEXT,
                        hashtags TEXT,
                        date TEXT,
                        imagePath TEXT
                    );
                """

        cursor.execute(schema)

        data = {
            'product': self.marketing_dict['name'],
            'description': self.marketing_dict['description'],
            'prompt': self.prompt,
            'trend': self.trend,
            'hashtags': self.marketing_dict['hashtags'],
            'date': self.marketing_dict['date'],
            'imagePath': metadata['imagePath']
        }

        # Check if a record with the same 'product' name already exists
        cursor.execute("SELECT id FROM products WHERE product = %s", (data['product'],))
        existing_record = cursor.fetchone()

        if existing_record is None:
            # Insert data if no existing record is found
            insert_query = """
                        INSERT INTO products (product, description, prompt, trend, hashtags, date, imagePath)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
            cursor.execute(insert_query, (
                data['product'], data['description'], data['prompt'], data['trend'], data['hashtags'],
                data['date'], metadata['imagePath']))
            conn.commit()
            print("Data inserted successfully.")
        else:
            # Update the existing record
            update_query = """
                UPDATE products 
                SET description=%s, prompt=%s, trend=%s, hashtags=%s, date=%s, imagePath=%s 
                WHERE product=%s
            """
            cursor.execute(update_query, (
                data['description'], data['prompt'], data['trend'], data['hashtags'], data['date'],
                metadata['imagePath'], data['product']))
            conn.commit()
            print(f"Data with product name {data['product']} updated successfully.")

        conn.close()


class Commerce:
    def __init__(self):
        pass
        # self.product_images = product_images
        # self.hashtags = hashtags
        # self.description = description
        # self.heading = heading

    @autolog
    def upload_to_printfy(self, image_path, metadata):
        shop_ids = ptfy.check_shops_id(API_KEY_PRINTIFY)
        for shop in shop_ids:
            shop_id = shop['id']
            image_id = ptfy.upload_image_to_printify(image_path, API_KEY_PRINTIFY)
            res = ptfy.create_product_printify(image_id, metadata, shop_id, API_KEY_PRINTIFY)
            ptfy.publish_product(shop_id, res['id'], API_KEY_PRINTIFY)

    def upload_to_ebay(self):
        pass

class Promotion:
    def __init__(self, description, design_image, trend):
        self.description = description
        self.design_image = design_image
        self.trend = trend

    def generate_promotional_material(self):
        # Generate Mock model wearing the shirt
        pass

    def ad_market_research(self):
        # analyze target audiance for ad
        pass

    def launch_ad_campain(self):
        # Intergrate with Google Ads API
        pass

    def upload_to_instagram(self):
        # Research API
        pass



# if __name__ == "__main__":
#     # Create the full pipeline (Define a fallback for DALLE-3)
#     # Setup the Flask server as A Local API With Ngrock (Or else)
#     # Try out LM Studio as a local LLM alternative
#
#     trends = pull_trends("finland")
#     filtered_trends = filter_trends(trends)
#     for trend in filtered_trends:
#         prompt = generate_prompt(trend)
#
#         image = ImageGen(trend=trend, prompt=prompt, db_name='my_database')
#         metadata = {}
#         while True:
#             try:
#                 metadata = image.generate_metadata()
#                 print(metadata)
#                 break
#             except:
#                 print("Error, trying again..")
#                 pass
#
#         metadata["trend"] = trend
#         print(f"{trend} - {prompt}")
#         img_path = image.create_img()
#         x2_image = image.upscale_image(img_path)
#         complete_img_path = f"complete_imgs/{trend}_complete_{time.time()}.png"
#         image.remove_background("temp/upscaled_2x.png", complete_img_path)
#         metadata["imagePath"] = complete_img_path
#         image.update_in_db(metadata)
#
#         if_upload = input("Upload%s")
#         if if_upload == 'y':
#             commerace = Commerce()
#             printify_products = commerace.upload_to_printfy(complete_img_path, metadata)
#
#             print("Finished test, uploaded")
#             break
#     #
#     # rootdir = r'C:\Users\0910m\PycharmProjects\Artsionic\images'
#     #
#     # for subdir, dirs, files in os.walk(rootdir):
#     #     for file in files:
#     #         print(os.path.join(subdir, file))
#     #         x2_image = upscale_image(os.path.join(subdir, file))
#     #         remove_background("upscaled_2x.png", f"complete_imgs/test/testing_{time.time()}.png"