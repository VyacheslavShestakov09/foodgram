import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для загрузки ингредиентов из CSV файла в базу данных."""
    help = 'Простое наполнение базы ингредиентами из CSV (без проверок)'

    def handle(self, *args, **options):
        file_path = os.path.abspath(
            os.path.join(
                settings.BASE_DIR, '..', 'data', 'ingredients.csv'
            )
        )
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR('Файл ingredients.csv не найден')
            )
            return

        with open(file_path, encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            ingredients = [
                Ingredient(
                    name=row[0].strip(),
                    measurement_unit=row[1].strip()
                )
                for row in reader
            ]

        Ingredient.objects.bulk_create(ingredients)

        self.stdout.write(self.style.SUCCESS(
            f'Загрузка завершена. Добавлено {len(ingredients)} ингредиентов.'
        ))
