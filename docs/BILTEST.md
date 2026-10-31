# Biltest: Night-färger, svenska Apps-rutor, städning

Förberett 2026-10-31. Alla jobb är byggda med sync2-auto-magic och generalrepeterade på en
simulerad SYNC med bilens egna filer, i ordningen nedan. Varje steg och båda ångra-jobben
verifierades byte för byte, även efter städningen. Inget har gått till bilen.

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

## Inte byggbart än (och vad som saknas)

| Del | Saknas |
|---|---|
| Fartrutan på kartan | `Map.swf` och `GPS.swf` dekompilerade (hur gränsen och GPS-farten nås), och fas R3: bevis att Fords egna skärmar tar emot ändringar |
| Nattskärmen, automatisk | Ändring i ramen (`AppConsole.swf`, laddas vid start: fas R8) efter R3 och R6 |
| Nattskärmen, för hand ("Natt"-ruta i Apps) | Koden för det mörka lagret och hur Fords mediadel ger låt och artist; går inte att provköra på Macen, bara i bilen. Nästa bygge |
| Temperaturen i klimatfliken | Ramen (R8) eller Fords `ClimateConsoleObject.swf`, efter R3 |
