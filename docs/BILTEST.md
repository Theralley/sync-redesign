# Biltest: Night-färger, svenska Apps-rutor, samtalshistoriken, städning

Förberett 2026-10-31. Alla jobb är byggda med sync2-auto-magic och generalrepeterade på en
simulerad SYNC med bilens egna filer. Inget har gått till bilen.

## Sjunde turens resultat (2026-11-04)

- `bundle-b2a0` kördes 15:53. Alla 8 delarna verifierade byte för byte. UNTITLED 2 (`bundle-de93`)
  behövdes inte och är oanvänd.
- Rasmus: bättre. Fotona visar bara kartan, så Hem är inte kontrollerat på bild: varken ramarna
  eller den lösa "Klimat".
- **CarPlay fungerar**, installerat med sync2-auto-magic: hemskärmen, tryck, Kartor med vägledning
  och Spotify genom bilens högtalare. Ljudet hördes med iPhonens Bluetooth på, så vägen är inte
  bevisad. Exit med CarPlay igång tar tillbaka SYNC. Siri och samtal är inte provade.
- **Öppet problem: SYNC 2 är väldigt långsamt.** Tryck i CarPlay kommer sent, bilden hackar, och
  Fords egna skärmar är också långsamma. Se sync2-auto-magics
  [PERFORMANCE.md](https://github.com/Theralley/sync2-auto-magic/blob/main/docs/PERFORMANCE.md).
- **Rättelse:** bilen har ingen backkamera, bara parkeringssensorer. Deras ruta kommer inte upp
  över AutoKit. Backtesterna nedan gäller nu den rutan.

## Sjunde turen: version 2 lagad (förberett 2026-11-03)

Sjätte turens tre fel, lagade:

- **Förinställningarnas ramar:** vi hade nollat storleken på klippet som temat ritar ramen i,
  men temat sätter tillbaka storleken när det ritar, så ramarna hamnade en rad för högt. Nu får
  klippen Fords egen placering igen, och ramen hamnar exakt på knappen (även Stör inte).
- **Inga knappkanter alls:** temats tunna kant runt varje knapp ritas nu helt genomskinlig, en
  enda siffra i ramens kod (100 till 0). Knapparna på klimat-, radio- och telefonskärmarna blir
  platta. Samma siffra styr också kanten på en avstängd knapp och röststyrningens markering av
  knappar man kan säga: de syns inte heller längre.
- **Den lösa "Klimat":** klimatetiketten hänger nedtill på skärmen, så när vi flyttade den 100
  px upp hamnade den i klimatkortet. Nu står den 600 px upp, långt ovanför skärmen.

Fyra filer ändras (ramen, klimatetiketten, mediahörnet och telefonhörnet), alla läses när SYNC
startar. Temat är oförändrat. Telefonens egen meny (glansiga bilder i Phone.swf) kommer senare.

- **SYNC-stickan:** `bundle-b2a0`: de fyra filerna först tillbaka till Fords, sedan lagade
  (8 delar).
- **UNTITLED 2:** `bundle-de93`: alla 14 filerna och färgerna tillbaka till Fords (15 delar).
  Dimningen, Apps-rutorna och samtalshistoriken ligger kvar.
- Generalrepeterat på en simulerad SYNC i bilens läge efter sjätte turen: på och av byte för
  byte, och även sjätte turens ångra (`bundle-6088`) tar bilen tillbaka till Fords efter detta.
  Ramen skiljer sig från bilens nuvarande i exakt en byte. Codex har granskat ändringarna: fynden
  gällde verktygens kontroller, inte filerna till bilen. Båda stickorna skrivna, lästa tillbaka
  efter ommontering, märkta och utmatade.

I bilen:

1. Parkerad, motorn igång. Stoppa i SYNC-stickan och vänta: "Install successfully completed",
   sedan startar SYNC om.
2. **Foto** av Hem (nära på mediakortet och klimatkortet), klimatskärmen, radion och telefonen.
3. Hem: sitter förinställningarnas ramar på knapparna nu, eller syns inga kanter alls? Är den
   lösa "Klimat" borta? Tryck på en förinställd station och Stör inte.
4. Prova som förut: samtal in och ut, klimatet (**MAX DEFROST**), **backen och parkeringssensorerna**,
   röstknappen.
5. Ser något fel ut: UNTITLED 2. Ta med fotona och båda stickorna till Macen.

## Sjätte turen: version 2, ram och Hem på ett rutnät (förberett 2026-11-03)

Femte turen såg fortfarande ut som det gamla systemet med nya färger, och korten på Hem satt
inte i linje. Version 2 bygger om ramen och Hem i stället för att måla om dem:

- **Hem:** fyra lika stora kort på ett rutnät, 8 px mellan och runt korten. Varje kort har en
  rubrik med ikon i områdets färg (Telefon, Navigation, Media, Klimat). Batteri och signal
  sitter till höger på telefonkortets rubrikrad. Kompassen är borta. Förinställningarna och
  sätesknapparna är platta och lite ljusare än kortet. Klimatkortet visar sätesknapparna mitt i
  kortet, eftersom bilen aldrig visar temperaturerna på Hem.
- **Listerna:** helt svarta, utan Fords flikar. På Hem visar listen upptill bara klockan och
  listen nedtill bara Info, Hem och Inställningar. Den valda knappen har ett tunt streck
  upptill. På alla andra skärmar står Telefon, Navigation, Media och Klimat kvar som förut,
  och ett samtal tar över precis som förut.
- **Menyerna** till vänster i Inställningar och Info är platta, utan glans.
- **Färgerna:** knapparnas kant i knappens egen färg och inga glödband, som förut, men
  knapparna är något ljusare så att de syns på korten.

Det är 14 av Fords filer, alla läses när SYNC startar, plus färgerna. Ingen ändring av det man
trycker på: knapparna sitter kvar och tar emot tryck som förut.

- **SYNC-stickan:** `bundle-6166`: femte turens färger, Hem och ram tillbaka till Fords, sedan de
  nya färgerna, Hems fyra hörn, listernas fem etiketter, Media.swf, de två menyerna, ramen och
  sist Hem (18 delar). Stannar något tidigare körs inget efter det.
- **UNTITLED 2:** `bundle-6088`: alla 14 filerna och färgerna tillbaka till Fords
  (15 delar). Dimningen, Apps-rutorna och samtalshistoriken ligger kvar.
- Generalrepeterat på en simulerad SYNC i bilens läge just nu: på och av, alla 33 delar byte för
  byte. Båda stickorna skrivna, lästa tillbaka efter ommontering, märkta och utmatade 2026-11-03.
- Codex har granskat s2am (inga fel) och verktygen. Fynden gällde verktygens kontroller, inte
  filerna till bilen: de två allvarliga är kontrollerade direkt i bilens filer.

I bilen:

1. Parkerad, motorn igång. Stoppa i SYNC-stickan och vänta: "Install successfully completed",
   sedan startar SYNC om. Det tar längre tid än förut (många filer).
2. **Foto** av Hem, Telefon, Klimat, kartan, Media och Inställningar > Display, och av Info.
   Gärna både i dagsljus och i mörker.
3. Hem: tryck mitt i varje kort (Telefon, Karta, Media och Klimat ska öppnas), en förinställd
   station, Stör inte och sätesvärmen (stängs den av igen?).
4. Prova: ett samtal in och ett ut (tar samtalet över skärmen?), radion, klimatet (temperatur,
   fläkt, A/C, **MAX DEFROST**), **backen och parkeringssensorerna**, röstknappen. På kartan: Mål och Meny.
5. Listerna: står klockan i mitten upptill på Hem, och står Telefon/Navigation/Media/Klimat kvar
   på de andra skärmarna? Ändra volymen på Hem: syns volymrutan?
6. **Om skärmen förblir svart eller Hem är tomt:** stoppa i UNTITLED 2 ändå och vänta två
   minuter. Installationstjänsten går vid sidan av skärmarna. Sedan mjuk omstart (vredet och ⏭
   i tio sekunder).
7. Ser något fel ut: UNTITLED 2. Ta med fotona och båda stickorna till Macen.

**Resultat (2026-11-03, cirka 12:50):** SYNC-stickan körd, alla 18 delar verifierade byte för
byte vid importen. Fotona visar version 2: fyra kort i rutnät med rubriker, svarta lister med bara
klockan upptill på Hem, platta menyer i Info och Inställningar, och etiketterna kvar på de andra
skärmarna. Klimatkortet visade temperaturerna på rubrikraden (klimatet var på). Rasmus: "under
media on 'home' some squres (white edges square) are off". Tre fel:
- Förinställningarnas tunna ljusa ramar ritas förskjutna, ungefär en rad upp, inte runt
  knapparna: temat ritar ramen själv och ställer tillbaka storleken vi nollade.
- En lös grå "Klimat" till höger om sätesknapparna i klimatkortet.
- Knapparna på områdenas skärmar (klimat, radio, telefon) har kvar Fords ljusgrå kant: bara
  systemets färg är kantlös i temat.

UNTITLED 2 behövdes inte.

## Femte turen: rak ram, nästan svart, Hem som kort (förberett 2026-11-02)

Fjärde turen visade att bilens skärm gör mörkgrått ljust, så allt flyttas närmare svart. Dessutom
kommer de första ändringarna av layouten:

- **Ramen:** listerna upptill och nedtill går raka över hela skärmen, utan Fords sneda mittbitar
  (klockans fält upptill; Info, Hem och Inställningar nedtill). Den valda knappen får ett grått
  streck upptill. Bara bilder byts: knapparna sitter kvar och tar emot tryck som förut.
- **Färgerna:** nästan svarta knappar och lister, knapparnas kant i knappens egen färg, och inga
  glödband i områdena (det gula randiga fältet uppe till vänster på Telefon försvinner).
- **Hem:** de fyra hörnen i var sitt kort med en färgad kant till vänster (telefon gul,
  navigering grön, media röd, klimat blå) på svart. Innehållet i korten är Fords, som förut. Hem
  läses när SYNC startar, precis som ramen.

- **SYNC-stickan:** `bundle-6bce`: Fords färger och ram tillbaka, sedan de nya färgerna, den
  raka ramen och sist Hem. Stannar något tidigare körs inget efter det.
- **UNTITLED 2:** `bundle-1b62`: Fords ram, Fords Hem och Fords färger. Dimningen, Apps-rutorna
  och samtalshistoriken ligger kvar.
- Generalrepeterat på en simulerad SYNC i bilens läge just nu: på och av byte för byte. Båda
  stickorna skrivna, lästa tillbaka efter ommontering, märkta och utmatade 2026-11-02.

I bilen:

1. Parkerad, motorn igång. Stoppa i SYNC-stickan och vänta: "Install successfully completed",
   sedan startar SYNC om.
2. **Foto** av Hem, Telefon (Samtalshistorik), Klimat, kartan och Inställningar > Display, gärna
   både i dagsljus och i mörker. Och med egna ögon: ser listerna och knapparna mörka ut?
3. Hem: tryck mitt i varje kort (Telefon, Karta, Media och Klimat ska öppnas), en förinställd
   station, Stör inte och sätesvärmen (stängs den av igen?).
4. Prova: ett samtal in och ett ut, radion, klimatet (temperatur, fläkt, A/C, **MAX DEFROST**),
   **backen och parkeringssensorerna**, röstknappen. På kartan: Mål och Meny.
5. Dimningen: Läge Auto, Autom. dimning På, tryck − fler än fem gånger, stäng Display och öppna
   den igen. Vad står förskjutningen på, och blev skärmen mörkare? + eller återställning tar
   tillbaka den.
6. **Om skärmen förblir svart eller Hem är tomt:** stoppa i UNTITLED 2 ändå och vänta två
   minuter. Installationstjänsten går vid sidan av skärmarna. Sedan mjuk omstart (vredet och ⏭
   i tio sekunder).
7. Ser något fel ut: UNTITLED 2. Ta med fotona och båda stickorna till Macen.

**Resultat (2026-11-02, cirka 16:30):** SYNC-stickan körd, alla fem delar verifierade byte för
byte (importerat 2026-11-03). Rasmus: "still very as the old. looks shit. not even align." Korten
på Hem satt förskjutna mot varandra och innehållet var Fords; se FINDINGS.md. UNTITLED 2 behövdes
inte. Därför version 2.

## Fjärde turen: ramen lagad, mörkare dimning (2026-11-02)

Tredje turens fel var vårt, inte Fords: bilder utan genomskinlighet fick 0 i en byte som bilen
läser som täckning, så knapparna och listerna ritades genomskinliga. Lagat, och ramen är
byggd om. Dessutom kan förskjutningen för automatisk dimning nu gå ner till −10 (Ford: −5).

- **SYNC-stickan:** `bundle-8d9d`: Display med golvet −10, Fords ram tillbaka, sedan den
  lagade ramen.
- **UNTITLED 2:** `bundle-724f`, som ångrar ramen och dimningen.

**Resultat (2026-11-02, 07:39):** SYNC-stickan körd, alla tre delar verifierade byte för byte.
SYNC startade om och fotona visar den lagade ramen: knappar och lister är heltäckande nu.
Men bilens skärm visar mörkgrått mycket ljusare än siffrorna: på dagsfotona blir svart cirka
42 av 255, listerna cirka 150 och knapparna cirka 210, lika ljust som Fords egen grå ram.
Därför ser det fortfarande ut som det gamla systemet med nya skal (Rasmus omdöme). Dimningen
under −5 är inte provad än. UNTITLED 2 behövdes inte.

## Tredje turen: ny stil på hela SYNC (förberett 2026-11-01)

Fords glansiga knappar, listerna upptill och nedtill och deras ikoner är bilder i en enda fil,
ramen (`AppConsole.swf`). Alla 135 är omritade platta i samma storlek: mörka knappar utan glans,
en vald knapp tonad i områdets färg med ett streck upptill, platta lister och våra ikoner. Ingen
kod ändras och ingenting flyttar sig, så klimatknapparna sitter där de sitter. Det syns på
**varje** skärm, men det är samma layout: de nya skärmarna från skisserna kommer efter detta.

Ramen läses när SYNC startar. Det är första gången vi byter en sådan fil, så:

- **SYNC-stickan:** `bundle-8fc9`. Den lägger först tillbaka Fords färger, sedan Night med
  knappar utan ram (knapparnas kantlinje i knappens egen färg), sist den nya ramen
  (`screen-8393`). Stannar något tidigare rörs ramen inte.
- **UNTITLED 2:** `bundle-f6bd`, som lägger tillbaka Fords ram och Fords färger. Svenska
  Apps-rutor och de stora raderna i samtalshistoriken ligger kvar.
- Generalrepeterat på en simulerad SYNC i bilens läge just nu: på och av byte för byte.
  Båda stickorna skrivna, lästa tillbaka efter omstickning och efter ommontering, märkta
  och utmatade 2026-11-01.

**Resultat (2026-11-01, kväll):** SYNC-stickan körd, allt verifierat byte för byte. SYNC startade
med den nya ramen och alla skärmar på fotona fungerar. Platta mörka flikar, rader och knappar
utan kant. Men klockans fält, flikarna nedtill och menyknapparna till vänster blev ljust
blågrå, och på Klimat blev ett band nedtill klarblått. Orsaken spåras i Fords kod; UNTITLED 2
behövdes inte.

I bilen:

1. Parkerad, motorn igång. Stoppa i SYNC-stickan och vänta: "Install successfully completed",
   sedan startar SYNC om.
2. **Foto** av Hem, Telefon, Media, Klimat och Navigering.
3. Prova: ett samtal in och ett ut, radion, klimatet (temperatur, fläkt, A/C, **MAX DEFROST**),
   **backen och parkeringssensorerna**, röstknappen.
4. **Om skärmen förblir svart:** stoppa i UNTITLED 2 ändå och vänta två minuter. Installations-
   tjänsten går vid sidan av skärmarna. Sedan mjuk omstart (vredet och ⏭ i tio sekunder).
5. Ser något fel ut: UNTITLED 2. Ta med fotona och stickorna till Macen.

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

**Resultat (2026-11-01, förmiddag):** fotot visar vår samtalshistorik, inte Fords: tre höga
rader i stället för fem, tunna pilar på bläddringsknapparna i stället för Fords fyllda
trianglar, och våra samtalsikoner. SYNC visar alltså en ändrad Ford-skärm. Ändringen syns
knappt eftersom allt runt listan (menyn till vänster, flikarna, listerna upptill och nedtill)
fortfarande är Fords. Stickorna är inte inlästa än.

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
- [ ] Backa: **parkeringssensorernas ruta** kommer upp.
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
- [ ] Telefon i övrigt, ett inkommande samtal och backen som vanligt.
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
