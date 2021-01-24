from django.core.management import BaseCommand

from elasticsearch_client.es import import_data


class Command(BaseCommand):
    help = "Loads elasticsearch data"

    def add_arguments(self, parser):
        parser.add_argument('path', type=str,
                            help="Indicates the path of data file to be added.")

    def handle(self, *args, **options):
        path = options["path"]
        res = import_data(path)
        print(res)
        self.stdout.write(self.style.SUCCESS("Successfully imported %d documents to elasticsearch" % res[0]))
