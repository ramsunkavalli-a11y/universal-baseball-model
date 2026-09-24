# Which players slip through the arrival model?

Descriptive out-of-sample next-year arrival errors; AE research candidate, not live forecast

Probabilities below are the AE research model: outage-aware, no explicit era flag.
They concern any MLB PA next year, not batting ability, WAR or eventual career success.
Original R probabilities and diagnostic features are retained in the JSON and player-case table.

## Examples

### low_probability_200pa

| Origin | Player | Level | Age | Current PA | Predicted arrival | Next MLB PA | Year 2 PA | Year 3 PA |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2017 | Juan Soto | A | 18 | 123 | 1.4% | 494 | 659 | 196 |
| 2021 | Ezequiel Duran | A+ | 22 | 471 | 1.6% | 220 | 439 | 285 |
| 2024 | Jac Caglianone | A+ | 21 | 126 | 1.7% | 232 | — | — |
| 2022 | Patrick Bailey | A+ | 23 | 325 | 1.7% | 353 | 448 | 452 |
| 2017 | Jeff McNeil | AAA | 25 | 194 | 2.9% | 248 | 567 | 209 |
| 2022 | José Caballero | AA | 25 | 141 | 3.0% | 280 | 483 | 370 |
| 2022 | Zach Neto | AA | 21 | 167 | 3.8% | 329 | 602 | 554 |
| 2021 | Michael Harris II | A+ | 20 | 420 | 4.1% | 441 | 539 | 470 |
| 2021 | Brian Serven | AAA | 26 | 276 | 4.3% | 205 | 23 | 71 |
| 2021 | CJ Abrams | AA | 20 | 183 | 4.4% | 302 | 614 | 602 |
| 2021 | Jeremy Peña | AAA | 23 | 160 | 4.4% | 558 | 634 | 650 |
| 2018 | Austin Nola | AAA | 28 | 262 | 4.4% | 267 | 184 | 194 |
| 2024 | Cam Smith | AA | 21 | 134 | 5.2% | 493 | — | — |
| 2017 | Ronny Rodríguez | AAA | 25 | 483 | 5.5% | 206 | 294 | 0 |
| 2018 | Adam Haseley | AA | 22 | 513 | 6.6% | 242 | 92 | 21 |
| 2024 | Liam Hicks | AA | 25 | 494 | 7.1% | 390 | — | — |
| 2018 | Matt Beaty | AAA | 25 | 128 | 7.5% | 268 | 54 | 234 |
| 2018 | Mike Yastrzemski | AAA | 27 | 491 | 7.8% | 411 | 225 | 532 |
| 2024 | Nick Kurtz | AA | 21 | 50 | 7.8% | 489 | — | — |
| 2024 | Robert Hassell III | AAA | 22 | 362 | 8.4% | 206 | — | — |
| 2024 | Ryan Ritter | AA | 23 | 373 | 8.5% | 207 | — | — |
| 2017 | Lourdes Gurriel Jr. | AA | 23 | 254 | 10.6% | 263 | 343 | 224 |
| 2022 | Luis Matos | A+ | 20 | 415 | 11.1% | 253 | 156 | 184 |
| 2021 | Joey Meneses | AAA | 29 | 369 | 11.5% | 240 | 657 | 313 |
| 2024 | Jake Mangum | AAA | 28 | 428 | 11.9% | 428 | — | — |
| 2021 | Nelson Velázquez | AA | 22 | 425 | 12.9% | 206 | 179 | 230 |
| 2022 | Henry Davis | AA | 22 | 255 | 12.9% | 255 | 122 | 283 |
| 2023 | Austin Martin | AAA | 24 | 282 | 13.9% | 257 | 181 | — |
| 2021 | JJ Bleday | AA | 23 | 468 | 15.3% | 238 | 303 | 642 |
| 2018 | Michael Chavis | AAA | 22 | 173 | 15.8% | 382 | 158 | 124 |

### highest_probability_nonarrivals

| Origin | Player | Level | Age | Current PA | Predicted arrival | Next MLB PA | Year 2 PA | Year 3 PA |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2024 | Juan Brito | AAA | 22 | 652 | 90.0% | 0 | — | — |
| 2023 | Jorbit Vivas | AAA | 22 | 612 | 89.6% | 0 | 66 | — |
| 2022 | Jorge Barrosa | AA | 21 | 553 | 84.5% | 0 | 18 | 77 |
| 2023 | Rafael Lantigua | AAA | 25 | 578 | 84.2% | 0 | 0 | — |
| 2023 | Eddys Leonard | AAA | 22 | 559 | 84.0% | 0 | 0 | — |
| 2022 | George Valera | AAA | 21 | 566 | 83.0% | 0 | 0 | 48 |
| 2022 | Malcom Nuñez | AAA | 21 | 493 | 82.0% | 0 | 0 | 0 |
| 2023 | Juan Brito | AAA | 21 | 555 | 80.7% | 0 | 0 | — |
| 2023 | Ronny Simon | AAA | 23 | 553 | 80.6% | 0 | 88 | — |
| 2022 | Connor Norby | AAA | 22 | 547 | 80.1% | 0 | 194 | 337 |
| 2024 | Deyvison De Los Santos | AAA | 21 | 583 | 79.7% | 0 | — | — |
| 2023 | Damiano Palmegiani | AAA | 23 | 557 | 78.3% | 0 | 0 | — |
| 2022 | Justyn-Henry Malloy | AAA | 22 | 591 | 77.5% | 0 | 230 | 127 |
| 2022 | Moisés Gómez | AAA | 23 | 501 | 77.3% | 0 | 0 | 0 |
| 2022 | Justin Dirden | AAA | 24 | 549 | 73.9% | 0 | 0 | 0 |
| 2023 | Tirso Ornelas | AAA | 23 | 552 | 73.9% | 0 | 16 | — |
| 2022 | Addison Barger | AAA | 22 | 526 | 73.8% | 0 | 225 | 502 |
| 2023 | Tsung-Che Cheng | AA | 21 | 535 | 72.8% | 0 | 7 | — |
| 2023 | Troy Johnston | AAA | 26 | 600 | 72.7% | 0 | 121 | — |
| 2021 | Ronaldo Hernández | AAA | 23 | 387 | 72.5% | 0 | 0 | 0 |
| 2022 | Blaine Crim | AAA | 25 | 588 | 69.8% | 0 | 0 | 74 |
| 2024 | Emmanuel Rodriguez | AAA | 21 | 209 | 69.8% | 0 | — | — |
| 2022 | Leandro Cedeño | AAA | 23 | 537 | 69.3% | 0 | 0 | 0 |
| 2022 | Andy Pages | AA | 21 | 571 | 69.0% | 0 | 443 | 624 |
| 2017 | Mauricio Dubón | AAA | 22 | 548 | 68.9% | 0 | 111 | 177 |
| 2022 | Blaze Alexander | AAA | 23 | 406 | 68.9% | 0 | 185 | 266 |
| 2023 | Ryan Ward | AAA | 25 | 615 | 68.7% | 0 | 0 | — |
| 2017 | Edwin Rios | AAA | 23 | 522 | 68.6% | 0 | 56 | 83 |
| 2021 | Micker Adolfo | AAA | 24 | 405 | 67.7% | 0 | 0 | 0 |
| 2017 | Andrew Pullin | AAA | 23 | 550 | 67.6% | 0 | 0 | 0 |

### largest_help

| Origin | Player | Level | Age | Current PA | Predicted arrival | Next MLB PA | Year 2 PA | Year 3 PA |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2021 | Will Benson | AAA | 23 | 439 | 32.4% | 61 | 329 | 388 |
| 2021 | Drew Waters | AAA | 22 | 459 | 31.3% | 109 | 337 | 19 |
| 2022 | Blake Rutherford | AAA | 25 | 467 | 30.5% | 36 | 0 | 0 |
| 2021 | Mark Vientos | AAA | 21 | 349 | 42.9% | 41 | 233 | 454 |
| 2021 | Símon Muzziotti | AAA | 22 | 83 | 40.6% | 9 | 0 | 0 |
| 2021 | Lucius Fox | AAA | 23 | 270 | 62.3% | 28 | 0 | 0 |
| 2022 | Matt McLain | AA | 22 | 452 | 52.9% | 403 | 0 | 577 |
| 2021 | Nick Allen | AAA | 22 | 380 | 28.8% | 326 | 329 | 105 |
| 2022 | Nathan Lukes | AAA | 27 | 484 | 28.6% | 31 | 91 | 438 |
| 2022 | Mason McCoy | AAA | 27 | 503 | 47.8% | 1 | 57 | 26 |
| 2021 | Marcus Wilson | AAA | 24 | 437 | 48.2% | 6 | 0 | 0 |
| 2021 | Alek Thomas | AAA | 21 | 495 | 71.8% | 411 | 402 | 103 |
| 2021 | Josh Jung | AAA | 23 | 342 | 38.2% | 102 | 515 | 188 |
| 2022 | Kyren Paris | AA | 20 | 452 | 24.0% | 46 | 59 | 140 |
| 2021 | Kyle Stowers | AAA | 23 | 530 | 42.3% | 98 | 33 | 209 |
| 2021 | José Azócar | AAA | 25 | 544 | 26.5% | 216 | 102 | 79 |
| 2021 | Jihwan Bae | AA | 21 | 372 | 33.7% | 37 | 371 | 81 |
| 2021 | Heliot Ramos | AAA | 21 | 495 | 73.5% | 22 | 60 | 518 |
| 2022 | Tristan Gray | AAA | 26 | 500 | 31.7% | 5 | 31 | 86 |
| 2022 | Zach Remillard | AAA | 28 | 491 | 27.9% | 160 | 39 | 0 |

### largest_harm

| Origin | Player | Level | Age | Current PA | Predicted arrival | Next MLB PA | Year 2 PA | Year 3 PA |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | Brett Harris | AAA | 25 | 461 | 18.4% | 123 | 84 | — |
| 2022 | Malcom Nuñez | AAA | 21 | 493 | 82.0% | 0 | 0 | 0 |
| 2022 | José Rodríguez | AA | 21 | 484 | 67.3% | 0 | 0 | 0 |
| 2022 | LJ Talley | AAA | 25 | 444 | 62.4% | 0 | 0 | 0 |
| 2022 | Yonathan Perlaza | AA | 23 | 547 | 61.7% | 0 | 0 | 0 |
| 2022 | Andy Pages | AA | 21 | 571 | 69.0% | 0 | 443 | 624 |
| 2022 | Blaze Alexander | AAA | 23 | 406 | 68.9% | 0 | 185 | 266 |
| 2022 | Grant Witherspoon | AAA | 25 | 471 | 57.2% | 0 | 0 | 0 |
| 2018 | LaMonte Wade Jr. | AAA | 24 | 495 | 25.1% | 69 | 44 | 381 |
| 2021 | Ronaldo Hernández | AAA | 23 | 387 | 72.5% | 0 | 0 | 0 |
| 2022 | Dustin Harris | AA | 22 | 382 | 61.5% | 0 | 7 | 43 |
| 2022 | Tyler Gentry | AA | 23 | 483 | 59.0% | 0 | 5 | 0 |
| 2022 | Pedro León | AAA | 24 | 504 | 56.4% | 0 | 21 | 0 |
| 2023 | Steward Berroa | AAA | 24 | 450 | 25.0% | 45 | 6 | — |
| 2022 | Allan Cerda | AA | 22 | 506 | 54.9% | 0 | 0 | 0 |
| 2022 | Robert Neustrom | AAA | 25 | 409 | 55.8% | 0 | 0 | 0 |
| 2022 | Paul McIntosh | AA | 24 | 383 | 53.3% | 0 | 0 | 0 |
| 2022 | Connor Norby | AAA | 22 | 547 | 80.1% | 0 | 194 | 337 |
| 2022 | Sandro Fabian | AAA | 24 | 380 | 63.0% | 0 | 5 | 0 |
| 2022 | Troy Johnston | AAA | 25 | 492 | 54.9% | 0 | 0 | 121 |

### 2021_low_probability_arrivals

| Origin | Player | Level | Age | Current PA | Predicted arrival | Next MLB PA | Year 2 PA | Year 3 PA |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2021 | Jason Delay | AAA | 26 | 98 | 0.9% | 167 | 187 | 19 |
| 2021 | Michael Siani | A+ | 21 | 408 | 1.0% | 24 | 6 | 334 |
| 2021 | Israel Pineda | A+ | 21 | 315 | 1.1% | 14 | 0 | 0 |
| 2021 | Matt Wallner | A+ | 23 | 300 | 1.5% | 65 | 254 | 261 |
| 2021 | Ezequiel Duran | A+ | 22 | 471 | 1.6% | 220 | 439 | 285 |
| 2021 | Michael Massey | A+ | 23 | 439 | 2.0% | 194 | 461 | 356 |
| 2021 | Ryan Aguilar | AA | 26 | 258 | 2.0% | 26 | 0 | 0 |
| 2021 | Francisco Alvarez | A+ | 19 | 400 | 2.1% | 14 | 423 | 342 |
| 2021 | Caleb Hamilton | AAA | 26 | 279 | 2.2% | 23 | 6 | 0 |
| 2021 | Livan Soto | AA | 21 | 450 | 2.2% | 59 | 12 | 16 |
| 2021 | Nate Eaton | A+ | 24 | 322 | 2.5% | 122 | 56 | 0 |
| 2021 | Christian Lopes | AAA | 28 | 219 | 2.6% | 10 | 0 | 0 |
| 2021 | Liover Peguero | A+ | 20 | 417 | 2.7% | 4 | 213 | 10 |
| 2021 | Chris Okey | AAA | 26 | 194 | 2.8% | 13 | 2 | 0 |
| 2021 | Esteban Quiroz | AAA | 29 | 280 | 3.0% | 47 | 0 | 0 |
| 2021 | Yainer Diaz | A+ | 22 | 412 | 3.3% | 9 | 377 | 619 |
| 2021 | Joe Dunand | AAA | 25 | 244 | 3.4% | 11 | 0 | 0 |
| 2021 | Elier Hernandez | AAA | 26 | 422 | 3.5% | 35 | 0 | 0 |
| 2021 | Corbin Carroll | A+ | 20 | 29 | 3.8% | 115 | 645 | 684 |
| 2021 | Ezequiel Tovar | A+ | 19 | 469 | 3.8% | 35 | 615 | 695 |
| 2021 | Chuckie Robinson | AA | 26 | 244 | 3.9% | 60 | 0 | 76 |
| 2021 | Vaughn Grissom | A+ | 20 | 380 | 3.9% | 156 | 80 | 114 |
| 2021 | Ben DeLuzio | AAA | 26 | 265 | 4.0% | 25 | 0 | 0 |
| 2021 | Michael Harris II | A+ | 20 | 420 | 4.1% | 441 | 539 | 470 |
| 2021 | Wynton Bernard | AAA | 30 | 351 | 4.1% | 42 | 0 | 0 |
| 2021 | Brian Serven | AAA | 26 | 276 | 4.3% | 205 | 23 | 71 |
| 2021 | CJ Abrams | AA | 20 | 183 | 4.4% | 302 | 614 | 602 |
| 2021 | Jeremy Peña | AAA | 23 | 160 | 4.4% | 558 | 634 | 650 |
| 2021 | Luis Liberato | AAA | 25 | 337 | 4.5% | 5 | 0 | 0 |
| 2021 | Garrett Mitchell | AA | 22 | 268 | 4.5% | 68 | 73 | 224 |

## Timing rather than ultimate failure

[
  {
    "origin": 2021,
    "high_probability_nonarrivals": 5,
    "arrived_in_year_2_or_3": 1,
    "no_mlb_pa_through_year_3": 4
  },
  {
    "origin": 2022,
    "high_probability_nonarrivals": 41,
    "arrived_in_year_2_or_3": 22,
    "no_mlb_pa_through_year_3": 19
  }
]

## Limits

- Outcome-selected examples are not evidence of systematic bias by themselves
- Descriptive slices overlap and are not independent tests or causal attribution
- Tree contributions allocate model log odds, not true baseball causes
- A roster-flag flip is sensitivity, not a validated revised forecast
- Only 2021/2022 used for three-year delay accounting; no protected outcomes
- Historical position is a diagnostic join, not an arrival-model input
