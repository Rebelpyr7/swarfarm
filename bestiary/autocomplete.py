from django.contrib.staticfiles.templatetags.staticfiles import static
from django.db.models import Q
from django.urls import reverse

from rest_framework import serializers, viewsets, renderers, pagination

from bestiary.models import Monster


class BestiaryAutocompletePagination(pagination.PageNumberPagination):
    page_size = 15
    max_page_size = 15


class BestiaryAutocompleteSerializer(serializers.ModelSerializer):
    text = serializers.SerializerMethodField()
    image_filename = serializers.SerializerMethodField()
    element = serializers.SerializerMethodField()
    archetype = serializers.SerializerMethodField()
    bestiary_url = serializers.SerializerMethodField()

    class Meta:
        model = Monster
        fields = [
            'id',
            'text',
            'image_filename',
            'element',
            'archetype',
            'base_stars',
            'can_awaken',
            'is_awakened',
            'bestiary_url',
        ]

    def get_text(self, instance):
        return str(instance)

    def get_image_filename(self, instance):
        return static('/herders/images/monsters/{}'.format(instance.image_filename))

    def get_element(self, instance):
        return instance.get_element_display()

    def get_archetype(self, instance):
        return instance.get_archetype_display()

    def get_bestiary_url(self, instance):
        return reverse('bestiary:detail', kwargs={'monster_slug': instance.bestiary_slug})


class BestiaryAutocomplete(viewsets.ReadOnlyModelViewSet):
    renderer_classes = [renderers.JSONRenderer]
    serializer_class = BestiaryAutocompleteSerializer
    pagination_class = BestiaryAutocompletePagination

    def get_queryset(self):
        qs = Monster.objects.filter(obtainable=True).order_by('element', 'is_awakened')
        search_terms = self.request.query_params.get('search')

        if search_terms:
            # Split the terms into words and build a Q object
            search_terms = search_terms.split(' ')
            query = Q()

            for term in search_terms:
                query.add(
                    Q(name__icontains=term) |
                    Q(awakens_from__name__icontains=term) |
                    Q(awakens_to__name__icontains=term) |
                    Q(element__startswith=term),
                    Q.AND
                )

            qs = qs.filter(query)

        return qs
