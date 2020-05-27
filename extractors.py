import requests
import re

class SpoonacularExtractor():
    def __init__(self):
        self.api_key = config.get("CONFIGURATION","yummly_app_id")
        self.urls = {'list_url': 'https://api.spoonacular.com/recipes/findByIngredients',
                     'recipe_url': 'https://api.spoonacular.com/recipes/{}/information'}

    def extract_list(self, ingredients=[]):
        if not ingredients:
            raise Exception('Ingredients list is empty')
        
        ingredients_string = ',+'.join(ingredients)
        params = {'apiKey': self.api_key,
                  'ranking': '2',
                  'ignorePantry': 'false',
                  'ingredients': ingredients_string}

        url = self.urls['list_url']
        list_response = requests.request("GET", url=url, params=params)
        recipe_list = list_response.json()
        return recipe_list

    def extract_recipe(self, id, nutrition='false'):
        params = {'apiKey': self.api_key,
                  'includeNutrition': nutrition}

        url = self.urls['recipe_url'].format(id)
        recipe_response = requests.request("GET", url=url, params=params)
        recipe_info = recipe_response.json()
        return recipe_info

    def remove_html_tags(self, raw_html):
        cleaner = re.compile('<.*?>')
        plain_text = re.sub(cleaner, '', raw_html)
        return plain_text

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
