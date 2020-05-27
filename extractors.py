import requests
import re

class YummlyExtractor():
    def __init__(self):
        self.url = 'https://yummly2.p.rapidapi.com/feeds/search'
        self.headers = {'x-rapidapi-host': 'yummly2.p.rapidapi.com',
                        'x-rapidapi-key': '5f032ce0acmsh944911b8d99d5dcp199441jsn9be35c34e285'}        

    def extract_list(self, ingredients=[]):
        if not ingredients:
            raise Exception('Ingredients list is empty')
        
        ingredients_string = ',+'.join(ingredients)
        query = {'q': ingredients_string,
                 'start': '0',
                 'maxResult': '10'}
        url, headers = self.url, self.headers

        response = requests.request("GET", url=url, headers=headers, params=query).json()
        recipe_list = response['feed']
        recipe_list = self.parse_list(recipe_list)
        return recipe_list

    def parse_list(self, recipe_list=[]):
        if not recipe_list:
            raise Exception('Recipe list is empty')

        parsed_list = []
        for recipe in recipe_list:
            recipe_dict = {}
            recipe_dict['name'] = recipe['display']['displayName']

            content = recipe['content']
            recipe_dict['prep_steps'] = content['preparationSteps']

            ingredients_info = content['ingredientLines']
            ingredient_list = [x['wholeLine'] for x in ingredients_info]
            recipe_dict['ingredients'] = ingredient_list
            parsed_list.append(recipe_dict)
        return parsed_list
