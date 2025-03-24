from django.core.management.base import BaseCommand
from stream.models import ClassData


class Command(BaseCommand):
    help = "Populate ClassData model with initial data"

    def handle(self, *args, **kwargs):
        # Static data from views.py
        CLASS_DATA = [
            {"id": 1, "Name": "advertising-board-big", "Turkish": "büyük reklam panosu"},
            {"id": 2, "Name": "advertising-board-small", "Turkish": "küçük reklam panosu"},
            {"id": 3, "Name": "brand-advertising-sign", "Turkish": "marka reklam tabelası"},
            {"id": 4, "Name": "broken-median", "Turkish": "bozuk refüj ", "Speech": "bozuk refüj raporlandı"},
            {"id": 5, "Name": "broken-road", "Turkish": "bozuk yol ", "Speech": "bozuk yol raporlandı"},
            {"id": 6, "Name": "broken-stone", "Turkish": "kırık taş ", "Speech": "kırık kaldırım taşı raporlandı"},
            {"id": 7, "Name": "clothes-piggy-bank", "Turkish": "giysi kumbarası"},
            {"id": 8, "Name": "drain-grid", "Turkish": "yağmur suyu ızgarası"},
            {"id": 9, "Name": "empty-garbage-container", "Turkish": "boş çöp konteyneri"},
            {"id": 10, "Name": "empty-trash-bin", "Turkish": "boş çöp kutusu"},
            {
                "id": 11,
                "Name": "full-garbage-bin",
                "Turkish": "dolu çöp kutusu ",
                "Speech": "dolu çöp kutusu raporlandı",
            },
            {
                "id": 12,
                "Name": "full-garbage-container",
                "Turkish": "dolu çöp konteyneri ",
                "Speech": "dolu çöp konteyneri raporlandı",
            },
            {"id": 13, "Name": "garbage", "Turkish": "çöp ", "Speech": "çöp raporlandı"},
            {"id": 14, "Name": "garbage-box", "Turkish": "çöp kutusu"},
            {"id": 15, "Name": "manhole-cover", "Turkish": "logar kapağı"},
            {"id": 16, "Name": "number-of-tree", "Turkish": "ağaç sayısı"},
            {
                "id": 17,
                "Name": "on-the-ground-thrown-garbage",
                "Turkish": "yere atılmış çöp ",
                "Speech": "yere atılmış çöp raporlandı",
            },
            {"id": 18, "Name": "parking-violation", "Turkish": "park ihlali ", "Speech": "park ihlali raporlandı"},
            {"id": 19, "Name": "pole-banner", "Turkish": "direk afişi"},
            {"id": 20, "Name": "pole-poster-board", "Turkish": "direk poster panosu"},
            {"id": 21, "Name": "poster-banner", "Turkish": "poster afiş"},
            {
                "id": 22,
                "Name": "pothole-critical",
                "Turkish": "kritik çukur ",
                "Speech": "kritik çukur raporlandı",
            },
            {
                "id": 23,
                "Name": "pothole-high",
                "Turkish": "yüksek seviyede çukur ",
                "Speech": "yüksek seviyede çukur raporlandı",
            },
            {
                "id": 24,
                "Name": "pothole-medium",
                "Turkish": "orta seviyede çukur ",
                "Speech": "orta seviyede çukur raporlandı",
            },
            {
                "id": 25,
                "Name": "pothole_low",
                "Turkish": "düşük seviyede çukur ",
                "Speech": "düşük seviyede çukur raporlandı",
            },
            {"id": 26, "Name": "road-crack", "Turkish": "yol çatlağı ", "Speech": "yol çatlağı raporlandı"},
            {"id": 27, "Name": "road-fault", "Turkish": "yol kusuru ", "Speech": "yol kusuru raporlandı"},
            {"id": 28, "Name": "road-hole", "Turkish": "yol çukuru ", "Speech": "yol çukuru raporlandı"},
            {"id": 29, "Name": "square-manhole-cover", "Turkish": "kare logar kapağı"},
            {"id": 30, "Name": "standing-billboard", "Turkish": "ayakta duran reklam panosu"},
            {"id": 31, "Name": "street-cat", "Turkish": "sokak kedisi"},
            {"id": 32, "Name": "street-dog", "Turkish": "sokak köpeği"},
            {"id": 33, "Name": "person", "Turkish": "insan"},
            {"id": 34, "Name": "car", "Turkish": "araba"},
            {"id": 35, "Name": "motorcycle", "Turkish": "motosiklet"},
            {"id": 36, "Name": "dog", "Turkish": "köpek"},
            {"id": 37, "Name": "cat", "Turkish": "kedi"},
            {"id": 38, "Name": "traffic light", "Turkish": "trafik ışığı"},
            {"id": 39, "Name": "fire hydrant", "Turkish": "yangın musluğu"},
        ]

        for item in CLASS_DATA:
            ClassData.objects.update_or_create(
                id=item["id"],
                defaults={"Name": item["Name"], "Turkish": item["Turkish"], "Speech": item.get("Speech", "")},
            )

        self.stdout.write(self.style.SUCCESS(f"Successfully populated {len(CLASS_DATA)} class data records"))
