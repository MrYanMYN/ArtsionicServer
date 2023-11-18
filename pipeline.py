import utils
import datetime
import time
import base64

def autoDailyGeneratePicsPipeline(regions, localQueue):
    trends = {}
    images = {}
    for region in regions:
        pulled_trends = utils.pull_trends(region)
        trends[region] = pulled_trends

    for k, v in trends.items():
        print(v)
        trends[k] = utils.filter_trends(v)

    for region, trends in trends.items():
        for trend in trends:
            metadate = {}
            prompt = utils.generate_prompt(trend)
            image = utils.ImageGen(trend=trend, prompt=prompt, db_name='my_database')
            img_path, b64img = image.create_img_dalle3_offical()
            current_date = datetime.date.today().strftime('%Y-%m-%d')
            metadata = {
                'description': "",
                'prompt': prompt,
                'trend': trend,
                'hashtags': "",
                'date': current_date,
                'imagePath': img_path}
            image.update_basic_marketing_dict(metadata)
            image.create_in_db_image()
            itemId = image.get_id("products", "prompt", prompt)
            metadata['b64_img'] = b64img
            images[itemId] = metadata

    localQueue.put(images)
    return trends, images


def generateImgPipeline(trend, local_queue):
    images = {}
    prompt = utils.generate_prompt(trend)
    image = utils.ImageGen(trend=trend, prompt=prompt, db_name='my_database')
    img_path, b64img = image.create_img()
    current_date = datetime.date.today().strftime('%Y-%m-%d')
    metadata = {
        'description': "",
        'prompt': prompt,
        'trend': trend,
        'hashtags': "",
        'date': current_date,
        'imagePath': img_path,
    }
    image.update_basic_marketing_dict(metadata)
    image.create_in_db_image()
    itemId = image.get_id("products", "prompt", prompt)
    metadata['b64_img'] = b64img
    metadata['image_object'] = image
    images[itemId] = metadata
    local_queue.put(images)


def generatePostPipeline(current_metadata, localQueue, metadata_id):
    global images
    img_obj = current_metadata['image_object']
    # img_obj.upscale_image(current_metadata['imagePath'])
    img_obj.upscale_img_via_api(current_metadata['imagePath'])
    complete_img_path = f"./complete_imgs/{current_metadata['trend']}_complete_{time.time()}.png"
    current_metadata['imagePath'] = complete_img_path
    # img_obj.remove_background('temp/upscaled_2x.png', complete_img_path)
    img_obj.remove_background_via_api('temp/upscaled_2x.png', complete_img_path)
    # Add here the complete_img_path to load the image into memory and switch the b64 field with the new image data
    # with open(complete_img_path, 'rb') as image_file:
    #     base64_bytes = base64.b64encode(image_file.read())
    #     current_metadata['b64_img'] = base64_bytes
    #     image_file.close()
    while True:
        try:
            metadata = img_obj.generate_metadata()
            print(metadata)
            current_metadata.update(metadata)
            img_obj.update_in_db_complete(current_metadata)
            break
        except:
            print("retrying metadata retrival!")
            pass
    localQueue.put({metadata_id: current_metadata})


def uploadPost(complete_img_path, metadata):
    commerace = utils.Commerce()
    printify_products = commerace.upload_to_printfy(complete_img_path, metadata)


def extendedTrendPullPipeline(regions):
    trends = {}
    for region in regions:
        regionTrendList = utils.extended_trends_pull(region)
        trends[region] = regionTrendList


