import json
import boto3
import base64

from PIL import Image
from io import BytesIO

def lambda_handler(event, context):
    
    # # Log some basic request info (but not payload)...
    # print(event['requestContext'])

    # Load and resize the image...
    body_bin = base64.b64decode(event['body'])
    image = Image.open(BytesIO(body_bin))
    image.thumbnail(size=(600,600))
    image_width, image_height = image.size
    print("Loaded image and processed to size: {} x {}".format(image_width, image_height) )

    # Get raw PNG of resized image for Rekognition
    image_png = BytesIO()
    image.save(image_png, format="PNG")

    # Perform rekognition...
    client = boto3.client('rekognition')
    response = client.detect_faces(
        Image={
            'Bytes': image_png.getvalue(),
        },
        Attributes=[
            'ALL',
        ]
    )
    
    # Create the output image...
    for face in response['FaceDetails']:

        # Face pixel position...
        top = int(face['BoundingBox']['Top'] * image_height)
        left = int(face['BoundingBox']['Left'] * image_width)
        width = int(face['BoundingBox']['Width'] * image_width)
        height = int(face['BoundingBox']['Height'] * image_height)

        # Face roll...
        roll = 360 - face['Pose']['Roll']
        
        # Emotion...
        emotion = face['Emotions'][0]['Type']

        # Get emoji, resize and place within the source image...
        image_emoji = Image.open( "./images/{}.png".format(emotion) )
        image_emoji = image_emoji.resize((width,height))
        image_emoji = image_emoji.rotate(roll)
        image.paste(image_emoji, (left,top), image_emoji)

        print("Processed found face...")
    
    # Export the image back to base64
    image_output = BytesIO()
    image.save(image_output, format="PNG")
    image_str = base64.b64encode(image_output.getvalue())
    base64_message = 'data:image/png;base64, ' + image_str.decode('ascii')

    print("Exported image to base64...")
        
    return {
        'statusCode': 200,
        'body': json.dumps(base64_message)
    }