"""
Test for the tags API
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def detail_tag(tag_id):
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a new user"""
    return get_user_model().objects.create_user(
        email=email,
        password=password
    )


def create_tag(user, name):
    """Create and return a tag"""
    return Tag.objects.create(user=user, name=name)


class PublicTagsApiTest(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTest(TestCase):
    """Test authenticated API requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags"""
        create_tag(user=self.user, name='Tag1')
        create_tag(user=self.user, name='Tag2')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_list_limited_user(self):
        """Test retrieving a list of tags is limited to authenticated user"""
        other_user = create_user('other@example.com')
        tag = create_tag(user=self.user, name='Tag1')
        create_tag(user=other_user, name='Tag2')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.filter(user=self.user)
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data, serializer.data)

    def test_update_tag(self):
        """Test for updating tag"""
        tag = create_tag(user=self.user, name='tag1')

        payload = {
            'name': 'tag2'
        }
        url = detail_tag(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])
        self.assertEqual(tag.user, self.user)

    def test_update_user_return_error(self):
        """Test for updating tag"""
        tag = create_tag(user=self.user, name='tag1')
        other_user = create_user('other@example.com')
        payload = {
            'user': other_user,
        }
        url = detail_tag(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.user, self.user)

    def test_delete_tag(self):
        """Test for deleting tags"""
        tag = create_tag(user=self.user, name='tag')

        url = detail_tag(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())

    def test_delete_other_user_tag_error(self):
        """Test for deleting other user tags gives error"""
        other_user = create_user('other@example.com')
        tag = create_tag(user=other_user, name='tag')

        url = detail_tag(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Tag.objects.filter(id=tag.id).exists())

    def test_filter_tags_assigned_to_recipes(self):
        """Test listing tags by those assigned to recipes."""
        in1 = Tag.objects.create(
            user=self.user, name='tag1'
        )
        in2 = Tag.objects.create(
            user=self.user, name='tag2'
        )
        recipe = Recipe.objects.create(
            title='Recipe',
            time_minutes=5,
            price=Decimal('2.50'),
            user=self.user
        )
        recipe.tags.add(in1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(in1)
        s2 = TagSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filter_tags_unique(self):
        """Test filtered tags returns a unique list"""
        in1 = Tag.objects.create(
            user=self.user, name='tag1'
        )
        recipe1 = Recipe.objects.create(
            title='Recipe1',
            time_minutes=5,
            price=Decimal('2.50'),
            user=self.user
        )
        recipe2 = Recipe.objects.create(
            title='Recipe2',
            time_minutes=5,
            price=Decimal('2.50'),
            user=self.user
        )
        recipe1.tags.add(in1)
        recipe2.tags.add(in1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = TagSerializer(in1)
        self.assertIn(s1.data, res.data)
        self.assertEqual(len(res.data), 1)
