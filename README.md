# Dating Text Evaluator

### Analyze dating text screenshots, chess.com style! Uses Google Gemini.
### Used for entertainment purposes only. The LLM takes in an image and spits out a json with info like message sides, classifications, colours and transcripts. The json is parsed and generates the final annotated image, rendering the classification badges, bubbles and text.
### Example Flow ###
## 1. Original Screenshot ##
![alt text](https://github.com/elvis-p1/text-evaluator/blob/d83a2ed3e2485b5cb8527c2af0c4bf7933cd6402/examples/ex1.webp "Original Screenshot")
## 2. Generated Annotated Image ##
![alt text](https://github.com/elvis-p1/text-evaluator/blob/main/examples/ex2.png?raw=true "Annotated Image Generated")
## 3. Analysis Table ##
Contains the count of each evaluation for each chatter, and their "ELO" rating, indicating how skillfully they messaged<br />
![alt text](https://github.com/elvis-p1/text-evaluator/blob/main/examples/ex3.png?raw=true "Analysis Table")

#### 📁 Images you upload go to the static/uploads directory 
###### Flask used for the backend with HTML and CSS frontend
