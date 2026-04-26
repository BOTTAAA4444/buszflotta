Okos Város: Járműflotta / Tömegközlekedés követése az "ELK Stack" segítségével

Cél: Egy városi buszflotta (vagy futárcég járműveinek) szimulálása és valós idejű követése. Egy Python szkript szimulálja a járműveket, amelyek folyamatosan küldik a telemetriai adataikat (GPS koordináták, aktuális sebesség, üzemanyagszint). Az adatokat a Logstash gyűjti be, majd továbbítja egy Elasticsearch adatbázisba. A valós idejű mozgás, az esetleges anomáliák és a flotta aktuális állapota egy interaktív, térképes Kibana dashboardon kerül vizualizálásra. A teljes adatáramlási és megjelenítési rendszer Docker konténerekben (Docker Compose) van összehangolva és telepítve.

Eszközök: Python, Logstash, Elasticsearch, Kibana, Docker Compose
