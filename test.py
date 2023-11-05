# import utils
# from datetime import date
#
# images = {}
#
# def check():
#     global trends, images
#     trends = {}
#     regions = ['finland']
#     for region in regions:
#         pulled_trends = utils.pull_trends(region)
#         trends[region] = pulled_trends
#
#     for k, v in trends.items():
#         print(v)
#         trends[k] = utils.filter_trends(v)
#
#
#     for region, trends in trends.items():
#         for trend in trends:
#             metadate = {}
#             prompt = utils.generate_prompt(trend)
#             image = utils.ImageGen(trend=trend, prompt=prompt, db_name='my_database')
#             img_path, b64img = image.create_img()
#             current_date = date.today().strftime('%Y-%m-%d')
#             metadata = {
#             'description': "",
#             'prompt': prompt,
#             'trend': trend,
#             'hashtags': "",
#             'date': current_date,
#             'imagePath': img_path}
#             image.update_basic_marketing_dict(metadata)
#             image.create_in_db_image()
#             itemId = image.get_id("products", "prompt", prompt)
#             metadata['b64_img'] = b64img
#             images[itemId] = metadata
#
#     return b64img
#
#
#
# print(check())
# print(images)
import queue
print("starting...")
new_q = queue.Queue(10)
a = new_q.get(timeout=5)
