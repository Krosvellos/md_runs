# Úkol 4: Návrh pokročilé architektury neuronové sítě

## MML1 Projekt: Predikce doby průchodu Mythic+ dungeonem (Pit of Saron) podle složení skupiny

Tento úkol je spíš teoretický. Mám se zamyslet, jaká pokročilá architektura neuronové sítě by se hodila na můj projekt z předchozích úkolů, a hlavně proč zrovna ta.

## 1. Připomenutí projektu

Predikuju dobu průchodu dungeonem Pit of Saron na úrovni klíče +16 (`clear_time_ms`). Je to regrese. Jeden řádek dat je jeden run, tedy skupina 5 hráčů (tank, healer a 3 DPS). U každého hráče znám jeho třídu (class), specializaci (spec), rasu (race) a item level (ilvl).

V předchozím úkolu mi vyšlo, že předpovědět se toho dá málo, nejlepší model měl R² jen kolem 0.04. Hlavní důvod je nejspíš ten, že data pokrývají jen špičkové EU hráče, takže gear i skill jsou hodně podobné a o výsledném čase rozhoduje spíš to, co v datech vůbec nemám (provedení, počet smrtí, volba trasy).

## 2. Hlavní problém, který chci vyřešit

Tři DPS hráče mám v datech jako sloupce `dps_1`, `dps_2` a `dps_3`. Jenže pořadí těch tří hráčů nic neznamená. Skupina s Magem na pozici `dps_1` a Rogue na `dps_2` je úplně stejná skupina jako Rogue na `dps_1` a Mage na `dps_2`. Pro klasický model (Random Forest, Ridge) to ale byly dva různé vstupy a signál jedné třídy se mi tím rozdrobil do tří sloupců (občas pak mezi důležité příznaky vyskočila i rasa, což nedává smysl, jelikož vývojáři běžně dbají na zanedbatelnosti takových rozdílů).

Klasické modely totiž pracují s pevným vektorem a o pořadí se nestarají, takže ho berou jako důležité. Jde je přimět, aby pořadí ignorovaly, ale to bych jim musel ručně vyrobit příznaky nezávislé na pořadí, třeba spočítat, kolik hráčů dané třídy ve skupině je. To už jsem částečně dělal. Druhá možnost je použít architekturu, která má rovnou v sobě, že vstup je množina, a tu chci popsat tady.

## 3. Navržená architektura: Set Transformer

Hlavní myšlenka je brát každého hráče jako jeden token (malý vektor) a celou skupinu jako množinu 5 tokenů. To přesně sedí na to, jak naše data vlastně vypadají, skupina je sada hráčů, ne uspořádaný seznam. Token by vznikl z naučených embeddingů pro class, spec a roli, k tomu ilvl. Embeddingy se mi tady líbí proto, že podobné specy si v takovém prostoru můžou být blízko, kdežto u one-hot je každý spec úplně zvlášť a žádnou podobnost nezachytí. Rasu jsem nakonec vynechal, minule mi jako důležitá nevyšla.

Ještě poznámka k množině: skupina není pět úplně zaměnitelných hráčů, tank a healer jsou pevné role (jeden a jeden), zaměnitelní jsou jen ti tři DPS mezi sebou. Takže nepodstatnost pořadí, o kterou mi jde, platí vlastně jen uvnitř DPS. Roli proto dávám do tokenu jako embedding a počítám s ní i při agregaci níž.

Na těch 5 tokenech pak použiju self-attention (query, key, value). To je hlavní věc, kvůli které tuhle architekturu volím, protože každý hráč se může podívat na ostatní a vztahy mezi hráči se tak propíšou do výsledku. Model bych přitom držel malý, na téhle hrstce dat by se větší jen přeučil.

Na konci potřebuju z 5 tokenů udělat jeden vektor za celou skupinu. Tady bych nechtěl jen průměr, ten by smazal rozdíl mezi rolemi, a přitom tank, healer a DPS působí na čas dost jinak. Set Transformer umí agregovat chytřeji, takže si tu informaci o rolích udrží, a právě kvůli tomu po něm sahám místo úplně jednoduché množinové sítě, co tokeny prostě sečte.

### Proč attention a ne něco jednoduššího

Nejjednodušší množinová síť (Deep Sets) zakóduje každého hráče zvlášť a pak je sečte. Problém je, že takový model nevidí vztahy mezi hráči, a ty v našem případě existují. Nejlepší příklad je spec Augmentation Evoker (Aug). Jeho celá náplň je posilovat ostatní DPS, takže sám o sobě moc nezmůže, ale ve skupině se silnými DPS je hodně užitečný. Model, který kóduje hráče izolovaně, tohle nezachytí, kdežto self-attention ano, protože nechá Aug zohlednit, kdo je ve zbytku skupiny. Tady si nejsem úplně jistý, jestli na to v datech bude dost příkladů, ale jako argument pro attention mi to dává smysl.

Ještě jedna věc k pozici. U obrázků a textu se k tokenům přidává informace o pozici, ale tady to dělat nechci, protože pozice hráče je přesně ta nedůležitá věc, které se chci zbavit.

## 4. Aktuální trendy (rešerše na internetu)

Koukal jsem, co je teď (2025 a 2026) v pokročilých architekturách populární, a snažil se vybrat to, co se mě vůbec týká.

Narazil jsem na FT-Transformer, kde se každý sloupec převede na token pro transformer. To je podobné tomu, co děláme s hráči (jen v podobě řádků). A pak na práce kolem normalizace množinových sítí (Set Norm), které řeší, že Deep Sets a Set Transformer se při větší hloubce trénují špatně. Pro nás to znamená, že model nemáme stavět zbytečně velký.

Největší dnešní téma jsou ale Mamba, state space modely a Mixture of Experts. Mamba a state space modely jsou spíš náhrada za attention u opravdu dlouhých sekvencí (klidně 100 000 tokenů), kde je běžný attention moc pomalý. Mixture of Experts zase řeší, jak mít obří model, ale počítat jen jeho část. Mě se ani jedno netýká, mám pět hráčů, takže žádný problém s délkou ani s velikostí modelu nemám.

## 5. Co od toho čekám

Výrazné zlepšení R² od téhle architektury nečekám, protože ten strop drží data, ne volba modelu. Nejlepší minule byl Random Forest s R² 0.043 a Set Transformer by ho nejspíš nepřekonal o moc, když ta informace v datech prostě není.

Přínos vidím jinde. Set Transformer správně počítá s tím, že skupina je množina, takže by neměl dělat tu chybu s pořadím DPS jako modely předtím. Embeddingy speců by se daly zobrazit a v ideálním případě by se podobné specy mohly trochu přiblížit. A u attention vah se dá aspoň zkusit podívat, na koho se model díval, i když interpretace attention není úplně spolehlivá.

Taky je potřeba dát pozor na přeučení. Random Forest se minule přeučil a transformer obecně chce víc dat, než mám. Proto by to chtělo spíš malý a dobře regularizovaný model než něco velkého. A pořád platí chronologický split z dřívějška.

## 6. Závěr

Pro můj projekt se podle mě nejvíc hodí Set Transformer, tedy model, který bere skupinu jako množinu hráčů a používá attention, aby každý hráč mohl koukat na ostatní. Vyřeší to hlavní slabinu s pořadím DPS, kterou klasické modely měly. Jako moderní srovnání bych ještě rád vyzkoušel TabPFN, i když je férové dodat, že ten jako klasický tabulkový model problém s pořadím DPS sám neřeší, takže ho beru čistě jako referenční laťku, ne jako náhradu návrhu.
