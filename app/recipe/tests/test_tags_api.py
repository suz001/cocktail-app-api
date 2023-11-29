"""
Tests for the tags API
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import (
    Tag,
    Recipe,
)
from recipe.serializers import TagSerializer


TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    """Create tag detail url"""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create a user"""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagApiTests(TestCase):
    """Test unauthenticated API request"""
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving tags"""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagApiTests(TestCase):
    """Teste authenticated API request"""
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving a list of tags."""
        Tag.objects.create(user=self.user, name='Wine')
        Tag.objects.create(user=self.user, name='Gin')

        res = self.client.get(TAGS_URL)
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test list of tags is limited to authenticataed user"""
        user2 = create_user(email='user2@example.com')
        Tag.objects.create(user=user2, name='Brandy')
        tag = Tag.objects.create(user=self.user, name='Vodka')

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """Test updating a tag:
        adding in view.pymixins.UpdateModelMixin"""
        tag = Tag.objects.create(user=self.user, name='Brandy')
        payload = {'name': 'Vodka'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting a tag: mixins.DestroyModelMixin in view"""
        tag = Tag.objects.create(user=self.user, name='Gin')
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tag_assigned_to_recipe(self):
        """Test listing tags to those assigned to recipe"""
        tag1 = Tag.objects.create(user=self.user, name='Gin')
        tag2 = Tag.objects.create(user=self.user, name='Rum')
        recipe = Recipe.objects.create(
            title='Mojito',
            time_minutes=7,
            price=Decimal(15.99),
            user=self.user,
        )
        recipe.tags.add(tag1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_uique(self):
        """Test filtered tags returns a unique list"""
        tag1 = Tag.objects.create(user=self.user, name='Gin')
        Tag.objects.create(user=self.user, name='Rum')
        recipe1 = Recipe.objects.create(
            title='Mojito',
            time_minutes=7,
            price=Decimal(15.99),
            user=self.user,
        )
        recipe2 = Recipe.objects.create(
            title='Gin Tonic',
            time_minutes=10,
            price=Decimal(20.99),
            user=self.user,
        )
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)