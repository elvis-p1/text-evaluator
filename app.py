#!/usr/bin/env python3

from flask import Flask, flash, request, redirect, url_for, render_template
from google import genai
from PIL import Image, ImageDraw, ImageFont
import io
import os
from pydantic import BaseModel
from werkzeug.utils import secure_filename


api_key = "API_KEY_HERE"
client = genai.Client(api_key=api_key)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'webp'}

# print(response.text)
# chat_info: TextInfo = response.parsed[0]
# for message in chat_info["messages"]:
#     print(message["text"])

# img_draw(chat_info)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Returns
def img_draw(image_file, file_name):
    
    my_file = Image.open(image_file)
    
    prompt = './static/prompt.txt'

    # Structure of the JSON object
    class Messages(BaseModel):
        side: str
        text: str
        bubble_colour: str
        text_colour: str
        classification: str
        
        def __getitem__(self, item):
            """Allows accessing model fields using dictionary-like indexing."""
            try:
                return getattr(self, item)
            except AttributeError:
                raise KeyError(f"'{item}' not found in model fields.")
            
    class ELORatings(BaseModel):
        side: str
        rating: int
        
        def __getitem__(self, item):
            """Allows accessing model fields using dictionary-like indexing."""
            try:
                return getattr(self, item)
            except AttributeError:
                raise KeyError(f"'{item}' not found in model fields.")
        
    class TextInfo(BaseModel):
        is_chat: int
        messages: list[Messages]
        opening_name: str
        side_colours: list[list[str]]
        side_text_colours: list[str]
        elo_ratings: list[ELORatings]
        background_colour: str
        
        def __getitem__(self, item):
            """Allows accessing model fields using dictionary-like indexing."""
            try:
                return getattr(self, item)
            except AttributeError:
                raise KeyError(f"'{item}' not found in model fields.")
            
    with open(prompt, 'r') as file:
        file_content = file.read()

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-05-20",
        contents=[my_file, file_content],
        config={
            # Make the output be a json object
            "response_mime_type": "application/json",
            "response_schema": list[TextInfo]
        }
    )
    
    chat_data: TextInfo = response.parsed[0]

    if chat_data["is_chat"] == 1:
        return None
    
    def wrap_text(text, font, max_width, draw):
        """
        Wraps text to fit within the max_width.
        """
        words = text.split()
        lines = [] # Holds each line in the text box
        current_line = [] # Holds each word in the current line under evaluation.

        for word in words:
            # Check the width of the current line with the new word added
            test_line = ' '.join(current_line + [word])
            width = draw.textlength(test_line, font=font)
            if width <= max_width:
                current_line.append(word)
            else:
                # If the line is too wide, finalize the current line and start a new one
                lines.append(' '.join(current_line))
                current_line = [word]

        # Add the last line
        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def draw_textbox(text, x, y, max_width, font, bg_colour, text_colour, padding):
        
        wrapped_lines = wrap_text(text, font, max_width, draw)
        
        # Calculate positions
        end_x, end_y = x + max_width, y + (24 * int(len(wrapped_lines))) # Ending position for the textbox

        # Dimensions for the background box
        background_box = [(x - padding, y - padding), (end_x + padding, end_y + padding)]

        # Draw background box
        draw.rounded_rectangle(background_box, 10, fill=bg_colour)

        # Draw multiline text
        description = ""
        for line in wrapped_lines:
            description += line + "\n"

        # Draw multiline text.
        draw.multiline_text((x, y), description, font=font, fill=text_colour, spacing=8)

    # initialize font
    font = ImageFont.FreeTypeFont("./static/fonts/OpenSansEmoji.ttf", size=16)  # Use default font if you don't have this
    
    left_colour = chat_data["side_colours"][0][0]
    right_colour = chat_data["side_colours"][1][0]
    left_text_colour = chat_data["side_text_colours"][0]
    right_text_colour = chat_data["side_text_colours"][1]
    # create empty image
    size_x = 800
    size_y = my_file.size[1] 
    print(size_y)
    img = Image.new(size=(size_x, size_y), mode='RGB', color=(255,255,255))
    draw = ImageDraw.Draw(img)
    
    box_width = size_x // 2
    
    # Positioning the textboxes on the left and right
    left_x = size_x // 20
    right_x = size_x - box_width - (size_x // 20)   
    
    start_y = 50
    padding = 6
    
    for message in chat_data["messages"]:
        classification_name = message["classification"].lower()
        classification_path = "./badges/" + classification_name + ".png"
        im2 = Image.open(classification_path)
        im2 = im2.resize((50, 50))
        im2.convert("RGBA")
        if message["side"] == "left":
            draw_textbox(message["text"], left_x, start_y, box_width, font, left_colour, left_text_colour, padding)
            img.paste(im2, (left_x + box_width + 50,  start_y), mask=im2)
        else:
            draw_textbox(message["text"], right_x, start_y, box_width, font, right_colour, right_text_colour, padding)
            img.paste(im2, (right_x - 100, start_y), mask=im2)
        
        start_y += round(len(wrap_text(message["text"], font, box_width, draw)) * (16*1.33) + 50)
    
    output = io.BytesIO()
    img.convert("RGBA").save(output, format='PNG')
    output.seek(0, 0)
    
    dir_path = "./static/uploads"
    file_name = file_name.split(".")[0] + "_alt." + file_name.split(".")[1]
    file_path = os.path.join(dir_path, file_name)
    img.save(file_path)
    
    return chat_data

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "elvis-loves-bacon"
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            chat_data = img_draw(file, filename)
            if chat_data:
                left_colour = chat_data["side_colours"][0][1]
                right_colour = chat_data["side_colours"][1][1]
                opening_name = chat_data["opening_name"]
                messages = chat_data["messages"]
                
                """
                Represent number of messages with classifications in order:
                
                Brilliant
                Great
                Best
                Excellent
                Good
                Book
                Inaccuracy
                Mistake
                Miss
                Blunder
                """
                left_classifications = [0] * 10
                right_classifications = [0] * 10
                for message in messages:
                    classification = message["classification"].casefold()
                    side = message["side"].casefold()
                    if classification == "brilliant":
                        if side == "left":
                            left_classifications[0] += 1
                        else:
                            right_classifications[0] += 1
                    elif classification == "brilliant":
                        if side == "left":
                            left_classifications[1] += 1
                        else:
                            right_classifications[1] += 1
                    elif classification == "great":
                        if side == "left":
                            left_classifications[2] += 1
                        else:
                            right_classifications[2] += 1
                    elif classification == "best":
                        if side == "left":
                            left_classifications[3] += 1
                        else:
                            right_classifications[3] += 1
                    elif classification == "excellent":
                        if side == "left":
                            left_classifications[4] += 1
                        else:
                            right_classifications[4] += 1
                    elif classification == "good":
                        if side == "left":
                            left_classifications[5] += 1
                        else:
                            right_classifications[5] += 1
                    elif classification == "book":
                        if side == "left":
                            left_classifications[6] += 1
                        else:
                            right_classifications[6] += 1
                    elif classification == "inaccuracy":
                        if side == "left":
                            left_classifications[7] += 1
                        else:
                            right_classifications[7] += 1
                    elif classification == "mistake":
                        if side == "left":
                            left_classifications[8] += 1
                        else:
                            right_classifications[8] += 1
                    elif classification == "blunder":
                        if side == "left":
                            left_classifications[9] += 1
                        else:
                            right_classifications[9] += 1
                left_elo = "-" 
                right_elo = "-"
                for elo in chat_data["elo_ratings"]:
                    if elo["side"] == "left":
                        left_elo = str(elo["rating"])
                    elif elo["side"] == "right":
                        right_elo = str(elo["rating"])
                flash('Image successfully uploaded and displayed below')
                return render_template('index.html', filename=filename, left_colour=left_colour, right_colour=right_colour, opening_name=opening_name, lefty=left_classifications, righty=right_classifications, left_elo=left_elo, right_elo=right_elo)
            flash('Image may not be a chat message screenshot')
            return redirect(request.url)
        else:
            flash('Allowed image file formats are: pdf, png, jpg, jpeg, webp')
            return redirect(request.url)
    return render_template("index.html")

@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename="uploads/" + filename.split(".")[0] + "_alt." + filename.split(".")[1], code=301))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)