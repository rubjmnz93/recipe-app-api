"""
Test for the ingredients API
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

TAGS_URL = reverse('recipe:ingredient-list')


def detail_ingredient(ingredient_id):
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a new user"""
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


def create_ingredient(user, name):
    """Create and return a ingredient"""
    return Ingredient.objects.create(user=user, name=name)


class PublicIngredientsApiTest(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTest(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving a list of ingredients"""
        create_ingredient(user=self.user, name='Ingredient1')
        create_ingredient(user=self.user, name='Ingredient2')

        res = self.client.get(TAGS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_list_limited_user(self):
        """Test retrieving a list of ingredients is limited to auth user"""
        other_user = create_user('other@example.com')
        ingredient = create_ingredient(user=self.user, name='Ingredient1')
        create_ingredient(user=other_user, name='Ingredient2')

        res = self.client.get(TAGS_URL)

        ingredients = Ingredient.objects.filter(user=self.user)
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data, serializer.data)

    def test_update_ingredient(self):
        """Test for updating ingredient"""
        ingredient = create_ingredient(user=self.user, name='ingredient1')

        payload = {
            'name': 'ingredient2'
        }
        url = detail_ingredient(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])
        self.assertEqual(ingredient.user, self.user)

    def test_update_user_return_error(self):
        """Test for updating ingredient"""
        ingredient = create_ingredient(user=self.user, name='ingredient1')
        other_user = create_user('other@example.com')
        payload = {
            'user': other_user,
        }
        url = detail_ingredient(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.user, self.user)

    def test_delete_ingredient(self):
        """Test for deleting ingredients"""
        ingredient = create_ingredient(user=self.user, name='ingredient')

        url = detail_ingredient(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def test_delete_other_user_ingredient_error(self):
        """Test for deleting other user ingredients gives error"""
        other_user = create_user('other@example.com')
        ingredient = create_ingredient(user=other_user, name='ingredient')

        url = detail_ingredient(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Ingredient.objects.filter(id=ingredient.id).exists())
