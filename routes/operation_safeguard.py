import logging
from collections import defaultdict
from flask import request, jsonify
from routes import app
import json
import ast
logger = logging.getLogger(__name__)



def challenge1_calc(data) :
    transformations = data.get("transformations")

    logger.info(transformations)
    encrypted_word = data.get("transformed_encrypted_word")

    words = encrypted_word.split()
    transformations = transformations[::-1]

    def process_words(words, transform):
        if transform == "mirror_words":

            for index, word in enumerate(words):
                words[index] = word[::-1]

        elif transform == "encode_mirror_alphabet":
            
            logger.info("hmmm")
            for index, word in enumerate(words):
                new_word = ""
                for i in range(len(word)):
                    if (word[i] >= 'a' and word[i] <= 'z') :
                        start = 'a'
                        end = 'z'
                    else :
                        start = 'A'
                        end = 'Z'
                    new_word += chr(ord(end) - (ord(word[i]) - ord(start)))

                words[index] = new_word
                logger.info(new_word)

            logger.info(words)
        elif transform == "toggle_case":

            for index, word in enumerate(words):
                new_word = ""
                for i in range(len(word)):
                    if (word[i] >= 'a' and word[i] <= 'z') :
                        start = 'a'
                        startOther = 'A'
                    else :
                        start = 'A'
                        startOther = 'a'
                    new_word += chr(ord(startOther) + (ord(word[i]) - ord(start)))
                words[index] = new_word
        elif transform == "swap_pairs":

            for index, word in enumerate(words):
                new_word = ""
                for i in range(0, len(word), 2):
                    new_word += word[i + 1]
                    new_word += word[i]
                if len(word) % 2:
                    new_word += word[-1]

                words[index] = new_word
        elif transform == "encode_index_parity":

            for index, word in enumerate(words):
                word_sz = len(word)
                odd_pointer = word_sz // 2
                even_pointer = 0
                new_word = ""
                for i in range(word_sz):
                    if i % 2:
                        new_word += word[odd_pointer]
                        odd_pointer += 1
                    else : 
                        new_word += word[even_pointer]
                        even_pointer += 1

                words[index] = new_word

        elif transform == "double_consonants":
            for index, word in enumerate(words):
                new_word = ""
                for i in range(len(word)):
                    if word[i] in set(['a', 'o', 'e', 'u', 'i']):
                        new_word += word[i]
                    elif i % 2 == 0:
                        new_word += word[i]
                words[index] = new_word
        
        return words
    
    for transform in transformations:
        unnested = [t.replace(")", "") for t in transform.split('(')]

        logger.info(unnested)
        for t in unnested:
            if t == 'x':
                continue
            words = process_words(words, t)
        

    final_word = " ".join(words)

    return final_word




def challenge2_calc(data) :
    return "a"

def challenge3_calc(data) :
    return "a"
def challenge4_calc(result1, result2, result3) :

    return "a"

@app.route('/operation-safeguard', methods=['POST'])
def operation_safeguard():
    data = request.get_json()
    logging.info("data sent for evaluation {}".format(data))
    
    challenge1_data = data.get("challenge_one")
    challenge2_data = data.get("challenge_two")
    challenge3_data = data.get("challenge_three")

    result1 = challenge1_calc(challenge1_data)
    result2 = challenge2_calc(challenge2_data)
    result3 = challenge3_calc(challenge3_data)

    result4 = challenge4_calc(result1, result2, result3)

    result = {"challenge_one": result1, "challenge_two": result2, "challenge_three": result3, "challenge_four": result4}
    logging.info("My result :{}".format(result))
    return json.dumps(result)
