# Biltest: Night-färger, svenska Apps-rutor, samtalshistoriken, städning

Förberett 2026-10-31. Alla jobb är byggda med sync2-auto-magic och generalrepeterade på en
simulerad SYNC med bilens egna filer. Inget har gått till bilen.

## Andra turen (2026-11-01)

Första turen gick igenom: alla delar ligger verifierade byte för byte, och ångra-stickan
återställde allt. Syntes gjorde bara Apps-rutorna. Night-färgerna kom på men syns knappt
(bara glöden och områdesknapparna ändras). Samtalshistoriken såg ut som förut, men det är
oklart om SYNC hade startat om innan den öppnades.

En använd sticka installerar inget igen: SyncExtPack döper om `install.bin` till
`installed.bin`. Därför är båda stickorna nu lagda med nya jobb:

- **SYNC-stickan:** `bundle-5dbf`, med Night, svenska rutor och stora rader i Senaste samtal
  (ingen städning den här gången).
- **UNTITLED 2:** `bundle-9ea6`, som ångrar allt.

I bilen:

1. Parkerad, tändningen på, telefonen ansluten via Bluetooth. Stoppa i SYNC-stickan.
2. Vänta: "Install successfully completed", sedan **startar SYNC om** (skärmen blir svart,
   Ford-loggan kommer). Öppna ingenting förrän SYNC är tillbaka.
3. **Telefon, Samtalshistorik**, med samtal i listan: tre stora rader per sida, eller fem som
   förut? **Ta ett foto.** Kontrollerna står under steg 7 nedan.
4. Ser något fel ut: stoppa i UNTITLED 2.
5. Ta med fotot och stickan eller stickorna till Macen.

## Allt på en gång (samlingsjobbet, första turen)

**SYNC-stickan** bar `bundle-1c35`, som körde fem jobb i en tur, i den här ordningen:

1. Night-färgerna (`theme-fd69`)
2. SyncExtPacks egen Apps-meny tillbaka (`appmenu-83d5`), för att
3. lägga på vår meny med svenska rutor (`appmenu-1e46`)
4. Senaste samtal med stora rader och våra ikoner (R3b, `screen-6ffe`)
5. Städning av s2am:s gamla jobbmappar (`clean-0831`)

Stoppar en del körs inget efter den, och Macen säger vilken och varför. Varje del verifieras
för sig när stickan importeras.

**UNTITLED 2** bar `bundle-8737`, som ångrade allt i en tur: Fords samtalshistorik,
SyncExtPacks egen Apps-meny och Fords färger.

I bilen:

1. Parkerad, tändningen på. Stoppa i SYNC-stickan och rör den inte förrän SYNC har startat
   om (en gång, efter alla delarna).
2. Gör kontrollerna nedan: Night (steg 1), svenska rutor (steg 3) och stora rader (steg 7).
3. Ser något fel ut: stoppa i UNTITLED 2. Startar inte skärmen alls: följ
   [RECOVERY.md](RECOVERY.md).
4. Ta SYNC-stickan till Macen, så importeras och verifieras allt.

Nedan står samma jobb ett och ett, om du hellre tar dem i delar.

## Så går varje tur

1. **Ett jobb per tur.** En sticka bär bara ett jobb åt gången.
2. Bilen står parkerad med tändningen på. Stoppa i stickan och rör den inte förrän SYNC är
   klar och har startat om (jobb 1–3 startar om SYNC, städningen gör det inte).
3. Gör kontrollerna för steget (nedan).
4. Ta stickan till Macen. Den importeras och verifieras, och nästa jobb läggs på.

Ser något fel ut: kör steget **ångra** (tabellen). Startar inte skärmen alls: följ
[RECOVERY.md](RECOVERY.md).

## Ordning

| # | Jobb | Vad det gör | Startar om | Ångra |
|---|---|---|---|---|
| 0 | (på Macen) | Importera Apps-menytestet `appmenu-a215` från stickan | | |
| 1 | `theme-fd69` | Night-färgerna (Theme.XML och fyra toningar) | Ja | `theme-78ed` |
| 2 | `appmenu-83d5` | SyncExtPacks egen Apps-meny tillbaka: steg 1 av 2 för svenska rutor | Ja | behövs inte (det är ursprunget) |
| 3 | `appmenu-1e46` | Vår Apps-meny igen, med svenska rutor i den nya ikonfamiljen | Ja | `appmenu-1742` |
| 4 | `clean-0831` | Tar bort s2am:s gamla jobbmappar på bilen (omkring 2,2 MB); backuperna stannar | Nej | behövs inte |
| 5 | `screen-78f6` | R3a: samtalshistoriken (Telefon, Senaste samtal) med våra ikoner; koden orörd | Ja | `screen-e9a6` |
| 6 | `screen-e9a6` | Ångra R3a: Fords samtalshistorik tillbaka. Visar att ångra fungerar i bilen innan koden ändras | Ja | |
| 7 | `screen-6ffe` | R3b: samtalshistoriken med stora rader (76 px, tre per sida, namnet 26 px) och våra ikoner | Ja | `screen-4dca` |

- Steg 2 och 3 hör ihop: vår meny kontrolleras mot SyncExtPacks egen. Körs steg 3 utan steg 2
  stoppar jobbet sig självt, och inget ändras.
- Steg 2–3 kan hoppas över om de engelska rutorna duger. Steg 4 kan tas när som helst sist.
- **Stickorna nu:** 32 GB (SYNC) bär steg 1, Night. 2 GB (UNTITLED 2, omformaterad och hel)
  bär ångra för Night, `theme-78ed`. Båda är lästa tillbaka byte för byte. Steg 0 är gjort:
  Apps-menyn är verifierad på bilen, 11 filer byte för byte.

## Kontroller i bilen

**Efter steg 1 (Night):**
- [ ] Färgerna har bytts: knappar och glöd per område (gul, grön, röd, blå).
- [ ] Klimat: alla knappar svarar, även **MAX defrost**, A/C, fläkt och stolvärme.
- [ ] Backa: **backkameran** kommer upp.
- [ ] Ett samtal (ring dig själv): samtalsrutan kommer upp och samtalet fungerar.
- [ ] Med strålkastarna på (eller i mörker): nattläget ser rätt ut.

**Efter steg 2:** Apps visar SyncExtPacks vanliga lista.

**Efter steg 3 (svenska rutor):**
- [ ] Apps visar rutorna på svenska: CarPlay, Video, Filer, Starta om och Alla appar.
- [ ] Video och Filer öppnas; "Alla appar" visar den vanliga listan. (Tryck inte på
      "Starta om" i onödan: den startar om SYNC.)

**Efter steg 4:** inget syns i bilen; importen på Macen listar vad som tagits bort.

**Efter steg 5 (R3a, första ändrade Ford-skärmen):**
- [ ] Telefon, Senaste samtal öppnas: listan, flikarna (Alla, Utgående, Inkommande, Missade).
- [ ] Nya ikoner: pilarna, den gröna luren vid "Ring", markeringarna för utgående, inkommande
      och missade samtal.
- [ ] Tryck på ett samtal och "Ring": samtalet går.
- [ ] Telefon i övrigt, ett inkommande samtal och backkameran som vanligt.
- [ ] Öppnas inte skärmen, eller ser den fel ut: ångra med `screen-e9a6`. Resten av SYNC
      påverkas inte; skärmen laddas bara när den öppnas.

**Efter steg 6:** Senaste samtal ser ut som förut (Fords egen).

**Efter steg 7 (R3b, stora rader):**
- [ ] Senaste samtal visar tre stora rader i stället för fem; namnen är större.
- [ ] Ikonen, namnet och pilarna står mitt i raden; bakgrunden fyller hela raden.
- [ ] Bläddra ner och upp: tre rader per sida. Under körning visar SYNC högst fyra sidor.
- [ ] Välj ett samtal och "Ring": samtalet går. Flikarna (Alla, Utgående, Inkommande, Missade)
      fungerar.
- [ ] Ser raderna fel ut (överlappar, text klipps): ångra med `screen-4dca`, och ta gärna ett
      foto först.

## Inte byggbart än (och vad som saknas)

| Del | Saknas |
|---|---|
| Fartrutan på kartan | `Map.swf` och `GPS.swf` dekompilerade (hur gränsen och GPS-farten nås), och fas R3: bevis att Fords egna skärmar tar emot ändringar |
| Nattskärmen, automatisk | Ändring i ramen (`AppConsole.swf`, laddas vid start: fas R8) efter R3 och R6 |
| Nattskärmen, för hand ("Natt"-ruta i Apps) | Koden för det mörka lagret och hur Fords mediadel ger låt och artist; går inte att provköra på Macen, bara i bilen. Nästa bygge |
| Temperaturen i klimatfliken | Ramen (R8) eller Fords `ClimateConsoleObject.swf`, efter R3 |
