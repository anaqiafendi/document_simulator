# ReceiptFaker template taxonomy — per-dimension report

**979 templates** classified across **14 dimensions**.

Every dimension below is a discrete axis: each template takes exactly one value from that dimension's group list. Labels are read directly from the site's own template definitions, so they are ground truth rather than inferred from images.

## Dimensions at a glance

| # | Dimension | Groups | Largest group | Share |
| --- | --- | ---: | --- | ---: |
| 1 | `layout_signature` | 469 | `HEADER\|ITEMS\|CUSTOM` | 3.5% |
| 2 | `money_row_order` | 94 | `ITEM` | 38.5% |
| 3 | `section_count` | 15 | `6` | 20.2% |
| 4 | `divider_style` | 7 | `DASHES` | 40.4% |
| 5 | `total_divider_style` | 7 | `NONE` | 52.9% |
| 6 | `total_emphasis` | 6 | `NONE` | 90.7% |
| 7 | `background_type` | 6 | `CRUMPLED_1` | 90.1% |
| 8 | `font_type` | 4 | `MERCHANT_COPY` | 92.0% |
| 9 | `logo_placement` | 4 | `TOP` | 79.0% |
| 10 | `barcode_placement` | 4 | `NONE` | 65.3% |
| 11 | `number_format` | 4 | `LEFT` | 91.5% |
| 12 | `header_alignment` | 4 | `CENTER` | 91.5% |
| 13 | `merchant_block_position` | 3 | `TOP` | 97.3% |
| 14 | `quantity_column` | 3 | `PRESENT` | 44.1% |

---

## `layout_signature`

**469 groups.** The ordered sequence of block types -- the layout itself.

*Where to see it:* Read top to bottom down the receipt. HEADER|ITEMS|CUSTOM is logo and address, then the purchase table, then a footer message.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `HEADER\|ITEMS\|CUSTOM` | 34 | 3.5% | [H-E-B-Receipt](https://www.receiptfaker.com/generate/H-E-B-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|DATE\|CUSTOM` | 23 | 2.3% | [Kroger-Receipt](https://www.receiptfaker.com/generate/Kroger-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM` | 22 | 2.2% | [HSBC-Receipt](https://www.receiptfaker.com/generate/HSBC-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM` | 21 | 2.1% | [Bambu-Receipt](https://www.receiptfaker.com/generate/Bambu-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM` | 18 | 1.8% | [Marsano-Receipt](https://www.receiptfaker.com/generate/Marsano-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 16 | 1.6% | [GNC-Receipt](https://www.receiptfaker.com/generate/GNC-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM` | 16 | 1.6% | [Netto-Receipt](https://www.receiptfaker.com/generate/Netto-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 14 | 1.4% | [Lucky-Receipt](https://www.receiptfaker.com/generate/Lucky-Receipt) |
| `HEADER\|DATE\|ITEMS\|PAYMENT\|BARCODE` | 14 | 1.4% | [Hotel-receipt](https://www.receiptfaker.com/generate/Hotel-receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM` | 14 | 1.4% | [PetSmart-Receipt](https://www.receiptfaker.com/generate/PetSmart-Receipt) |
| `HEADER\|DATE\|ITEMS\|PAYMENT\|CUSTOM` | 12 | 1.2% | [Hy-Vee-Receipt](https://www.receiptfaker.com/generate/Hy-Vee-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 12 | 1.2% | [Dior-Receipt](https://www.receiptfaker.com/generate/Dior-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM` | 11 | 1.1% | [Belk-Receipt](https://www.receiptfaker.com/generate/Belk-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 11 | 1.1% | [GIANT-Receipt](https://www.receiptfaker.com/generate/GIANT-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM` | 10 | 1.0% | [Oasis-Receipt](https://www.receiptfaker.com/generate/Oasis-Receipt) |
| `HEADER\|DATE\|ITEMS\|CUSTOM` | 9 | 0.9% | [Subway-Receipt](https://www.receiptfaker.com/generate/Subway-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 9 | 0.9% | [Grill'd-Receipt](https://www.receiptfaker.com/generate/Grill'd-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 8 | 0.8% | [Londis-Receipt](https://www.receiptfaker.com/generate/Londis-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 8 | 0.8% | [SPAR-Store-Receipt](https://www.receiptfaker.com/generate/SPAR-Store-Receipt) |
| `HEADER\|PAYMENT\|CUSTOM` | 8 | 0.8% | [Amano-Receipt](https://www.receiptfaker.com/generate/Amano-Receipt) |
| `HEADER\|DATE\|ITEMS\|CUSTOM\|CUSTOM` | 7 | 0.7% | [Cabela's-Receipt](https://www.receiptfaker.com/generate/Cabela's-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 7 | 0.7% | [Flunch-Receipt](https://www.receiptfaker.com/generate/Flunch-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 7 | 0.7% | [JCPenney-Receipt](https://www.receiptfaker.com/generate/JCPenney-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 7 | 0.7% | [Pret-UK-Receipt](https://www.receiptfaker.com/generate/Pret-UK-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 6 | 0.6% | [Towing-Receipt](https://www.receiptfaker.com/generate/Towing-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 6 | 0.6% | [Plachutta-Receipt](https://www.receiptfaker.com/generate/Plachutta-Receipt) |
| `HEADER\|BARCODE\|DATE\|ITEMS\|PAYMENT\|CUSTOM` | 6 | 0.6% | [Bakery-Receipt](https://www.receiptfaker.com/generate/Bakery-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE\|DATE` | 6 | 0.6% | [Notary-Receipt](https://www.receiptfaker.com/generate/Notary-Receipt) |
| `CUSTOM\|HEADER\|CUSTOM\|ITEMS\|PAYMENT\|DATE\|CUSTOM` | 6 | 0.6% | [Walmart-Receipt](https://www.receiptfaker.com/generate/Walmart-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 6 | 0.6% | [Gucci-Receipt](https://www.receiptfaker.com/generate/Gucci-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 5 | 0.5% | [MIU-MIU-Receipt](https://www.receiptfaker.com/generate/MIU-MIU-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 5 | 0.5% | [Vet-Receipt](https://www.receiptfaker.com/generate/Vet-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 5 | 0.5% | [Rona-Receipt](https://www.receiptfaker.com/generate/Rona-Receipt) |
| `HEADER\|ITEMS` | 5 | 0.5% | [LOTII-Bakehouse](https://www.receiptfaker.com/generate/LOTII-Bakehouse) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 5 | 0.5% | [GDK-Receipt](https://www.receiptfaker.com/generate/GDK-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM` | 5 | 0.5% | [Neosurf-Receipt](https://www.receiptfaker.com/generate/Neosurf-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM` | 5 | 0.5% | [Vons-Receipt](https://www.receiptfaker.com/generate/Vons-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM` | 4 | 0.4% | [GOAT-Receipt](https://www.receiptfaker.com/generate/GOAT-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|CUSTOM` | 4 | 0.4% | [Buc-ee's-Receipt](https://www.receiptfaker.com/generate/Buc-ee's-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 4 | 0.4% | [Wagamama-Receipt](https://www.receiptfaker.com/generate/Wagamama-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 4 | 0.4% | [Lush-Receipt](https://www.receiptfaker.com/generate/Lush-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|DATE\|BARCODE` | 4 | 0.4% | [Lawyer-Receipt](https://www.receiptfaker.com/generate/Lawyer-Receipt) |
| `HEADER\|DATE\|RESTAURANT\|ITEMS\|PAYMENT\|CUSTOM` | 4 | 0.4% | [Car-Repair-Receipt](https://www.receiptfaker.com/generate/Car-Repair-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 4 | 0.4% | [Galp-Portugal-Receipt](https://www.receiptfaker.com/generate/Galp-Portugal-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 4 | 0.4% | [Grailed-Receipt](https://www.receiptfaker.com/generate/Grailed-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM` | 4 | 0.4% | [MUJI-Retail-Receipt](https://www.receiptfaker.com/generate/MUJI-Retail-Receipt) |
| `HEADER\|RESTAURANT\|ITEMS\|PAYMENT\|CUSTOM` | 4 | 0.4% | [Zomato-Receipt](https://www.receiptfaker.com/generate/Zomato-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|CUSTOM` | 4 | 0.4% | [Spaghetti-House-Receipt](https://www.receiptfaker.com/generate/Spaghetti-House-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|DATE\|BARCODE` | 4 | 0.4% | [Moving-Receipt](https://www.receiptfaker.com/generate/Moving-Receipt) |
| `HEADER\|DATE\|RESTAURANT\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 3 | 0.3% | [Ace-Receipt](https://www.receiptfaker.com/generate/Ace-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 3 | 0.3% | [Arby's-Receipt](https://www.receiptfaker.com/generate/Arby's-Receipt) |
| `HEADER\|ITEMS\|BARCODE\|CUSTOM` | 3 | 0.3% | [BIG-W-Receipt](https://www.receiptfaker.com/generate/BIG-W-Receipt) |
| `HEADER\|CUSTOM\|DATE\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 3 | 0.3% | [Nanny-Receipt](https://www.receiptfaker.com/generate/Nanny-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM` | 3 | 0.3% | [ZARA-Receipt](https://www.receiptfaker.com/generate/ZARA-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM` | 3 | 0.3% | [Toby-Carvery-Receipt](https://www.receiptfaker.com/generate/Toby-Carvery-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM` | 3 | 0.3% | [PAK'nSAVE-Receipt](https://www.receiptfaker.com/generate/PAK'nSAVE-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 3 | 0.3% | [Dunkin'-UK-Receipt](https://www.receiptfaker.com/generate/Dunkin'-UK-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE\|DATE` | 3 | 0.3% | [Clinic-Receipt](https://www.receiptfaker.com/generate/Clinic-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 3 | 0.3% | [O!Save-Receipt](https://www.receiptfaker.com/generate/O!Save-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM` | 3 | 0.3% | [Waffle-House-Receipt](https://www.receiptfaker.com/generate/Waffle-House-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS` | 3 | 0.3% | [DNA-Sports-Receipt](https://www.receiptfaker.com/generate/DNA-Sports-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS` | 3 | 0.3% | [Five-Guys-Receipt](https://www.receiptfaker.com/generate/Five-Guys-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|DATE` | 3 | 0.3% | [Law-Firm-Receipt](https://www.receiptfaker.com/generate/Law-Firm-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 3 | 0.3% | [GameStop-Receipt](https://www.receiptfaker.com/generate/GameStop-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE` | 3 | 0.3% | [Primark-Manchester-Receipt](https://www.receiptfaker.com/generate/Primark-Manchester-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|CUSTOM\|CUSTOM` | 3 | 0.3% | [Hisana-Receipt](https://www.receiptfaker.com/generate/Hisana-Receipt) |
| `HEADER\|DATE\|CUSTOM\|ITEMS\|CUSTOM` | 3 | 0.3% | [IHOP-Receipt](https://www.receiptfaker.com/generate/IHOP-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM` | 3 | 0.3% | [London-Drugs-Receipt](https://www.receiptfaker.com/generate/London-Drugs-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 3 | 0.3% | [Icicles-Receipt](https://www.receiptfaker.com/generate/Icicles-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|BARCODE\|CUSTOM\|CUSTOM` | 3 | 0.3% | [TGI-Fridays-Receipt](https://www.receiptfaker.com/generate/TGI-Fridays-Receipt) |
| `HEADER\|CUSTOM` | 3 | 0.3% | [Kmart-Receipt](https://www.receiptfaker.com/generate/Kmart-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM` | 3 | 0.3% | [Spec's-Receipt](https://www.receiptfaker.com/generate/Spec's-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|DATE\|BARCODE` | 3 | 0.3% | [Storage-Receipt](https://www.receiptfaker.com/generate/Storage-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM` | 2 | 0.2% | [BurgerFi-Receipt](https://www.receiptfaker.com/generate/BurgerFi-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [Barnes-and-Noble-Receipt](https://www.receiptfaker.com/generate/Barnes-and-Noble-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [True-Value-Receipt](https://www.receiptfaker.com/generate/True-Value-Receipt) |
| `HEADER\|RESTAURANT\|ITEMS\|CUSTOM` | 2 | 0.2% | [All-Saints-Receipt](https://www.receiptfaker.com/generate/All-Saints-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Nordsee-Receipt](https://www.receiptfaker.com/generate/Nordsee-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|ITEMS\|CUSTOM` | 2 | 0.2% | [Pep-Boys-Receipt](https://www.receiptfaker.com/generate/Pep-Boys-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Woolworths-Grocery-Receipt](https://www.receiptfaker.com/generate/Woolworths-Grocery-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 2 | 0.2% | [Big-Lots-Receipt](https://www.receiptfaker.com/generate/Big-Lots-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE` | 2 | 0.2% | [Apple-Receipt](https://www.receiptfaker.com/generate/Apple-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM` | 2 | 0.2% | [BP-Express-Receipt](https://www.receiptfaker.com/generate/BP-Express-Receipt) |
| `HEADER\|RESTAURANT\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 2 | 0.2% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `HEADER\|ITEMS\|BARCODE\|CUSTOM\|ITEMS\|CUSTOM` | 2 | 0.2% | [Pepco-Receipt](https://www.receiptfaker.com/generate/Pepco-Receipt) |
| `HEADER\|ITEMS\|BARCODE\|CUSTOM\|CUSTOM` | 2 | 0.2% | [BandM-Store-Receipt](https://www.receiptfaker.com/generate/BandM-Store-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [Paperchase-Receipt](https://www.receiptfaker.com/generate/Paperchase-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS` | 2 | 0.2% | [Stew-Leonard's-Receipt](https://www.receiptfaker.com/generate/Stew-Leonard's-Receipt) |
| `HEADER\|DATE\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM` | 2 | 0.2% | [Best-Havasu-Hardware-Receipt](https://www.receiptfaker.com/generate/Best-Havasu-Hardware-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|PAYMENT\|CUSTOM` | 2 | 0.2% | [Hiltl-Dachterrasse-Receipt](https://www.receiptfaker.com/generate/Hiltl-Dachterrasse-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS` | 2 | 0.2% | [Blend-Receipt](https://www.receiptfaker.com/generate/Blend-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Books-A-Million-Receipt](https://www.receiptfaker.com/generate/Books-A-Million-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Boots-Receipt](https://www.receiptfaker.com/generate/Boots-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Bunnings-Warehouse-Receipt](https://www.receiptfaker.com/generate/Bunnings-Warehouse-Receipt) |
| `HEADER\|CUSTOM\|RESTAURANT\|ITEMS\|PAYMENT\|CUSTOM` | 2 | 0.2% | [Pandora-Receipt](https://www.receiptfaker.com/generate/Pandora-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|PAYMENT\|CUSTOM` | 2 | 0.2% | [GAGA-Receipt](https://www.receiptfaker.com/generate/GAGA-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|PAYMENT\|PAYMENT\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Caffellini-Receipt](https://www.receiptfaker.com/generate/Caffellini-Receipt) |
| `HEADER\|DATE\|ITEMS\|CUSTOM\|BARCODE` | 2 | 0.2% | [Car-Wash-Receipt](https://www.receiptfaker.com/generate/Car-Wash-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM` | 2 | 0.2% | [Daycare-Receipt](https://www.receiptfaker.com/generate/Daycare-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [Five-Below-Receipt](https://www.receiptfaker.com/generate/Five-Below-Receipt) |
| `HEADER\|CUSTOM\|ITEMS` | 2 | 0.2% | [Salt-and-Straw-Receipt](https://www.receiptfaker.com/generate/Salt-and-Straw-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Chick-fil-A-Receipt](https://www.receiptfaker.com/generate/Chick-fil-A-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM` | 2 | 0.2% | [Chinatown-Point-KFC-Receipt](https://www.receiptfaker.com/generate/Chinatown-Point-KFC-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM` | 2 | 0.2% | [Modern-POS-Template](https://www.receiptfaker.com/generate/Modern-POS-Template) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM` | 2 | 0.2% | [Cityhallen-Receipt](https://www.receiptfaker.com/generate/Cityhallen-Receipt) |
| `HEADER\|DATE\|CUSTOM\|ITEMS\|CUSTOM\|PAYMENT\|CUSTOM\|BARCODE` | 2 | 0.2% | [Courier-Service-Receipt](https://www.receiptfaker.com/generate/Courier-Service-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [Media-Markt-Receipt](https://www.receiptfaker.com/generate/Media-Markt-Receipt) |
| `HEADER\|PAYMENT\|CUSTOM\|CUSTOM\|PAYMENT\|CUSTOM` | 2 | 0.2% | [Farley's-Receipt](https://www.receiptfaker.com/generate/Farley's-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [DSW-Receipt](https://www.receiptfaker.com/generate/DSW-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [Denner-Receipt](https://www.receiptfaker.com/generate/Denner-Receipt) |
| `HEADER\|DATE\|ITEMS\|PAYMENT` | 2 | 0.2% | [Denny's-PickUp-Receipt](https://www.receiptfaker.com/generate/Denny's-PickUp-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM\|DATE` | 2 | 0.2% | [Dentist-Receipt](https://www.receiptfaker.com/generate/Dentist-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 2 | 0.2% | [Patel-Brothers-Receipt](https://www.receiptfaker.com/generate/Patel-Brothers-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 2 | 0.2% | [Eric-Kayser-Receipt](https://www.receiptfaker.com/generate/Eric-Kayser-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Kinney-Drugs-Receipt](https://www.receiptfaker.com/generate/Kinney-Drugs-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 2 | 0.2% | [PureGym-Receipt](https://www.receiptfaker.com/generate/PureGym-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|BARCODE\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Fenwick-Receipt](https://www.receiptfaker.com/generate/Fenwick-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [Levi's-Receipt](https://www.receiptfaker.com/generate/Levi's-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE\|DATE` | 2 | 0.2% | [Gas-Receipt](https://www.receiptfaker.com/generate/Gas-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [GetGo-Receipt](https://www.receiptfaker.com/generate/GetGo-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Giant-Eagle-Receipt](https://www.receiptfaker.com/generate/Giant-Eagle-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|BARCODE` | 2 | 0.2% | [Harris-Teeter-Receipt](https://www.receiptfaker.com/generate/Harris-Teeter-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM` | 2 | 0.2% | [Hemingways-Receipt](https://www.receiptfaker.com/generate/Hemingways-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 2 | 0.2% | [TJ-Maxx-Receipt](https://www.receiptfaker.com/generate/TJ-Maxx-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Vans-Receipt](https://www.receiptfaker.com/generate/Vans-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Swatch-Receipt](https://www.receiptfaker.com/generate/Swatch-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 2 | 0.2% | [Micro-Center-Receipt](https://www.receiptfaker.com/generate/Micro-Center-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Wawa-Receipt](https://www.receiptfaker.com/generate/Wawa-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Printemps-Receipt](https://www.receiptfaker.com/generate/Printemps-Receipt) |
| `HEADER\|CUSTOM\|DATE\|CUSTOM\|ITEMS\|PAYMENT` | 2 | 0.2% | [Yellow-Cab-Receipt](https://www.receiptfaker.com/generate/Yellow-Cab-Receipt) |
| `HEADER\|DATE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Lyft-Receipt](https://www.receiptfaker.com/generate/Lyft-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [Maverik-Receipt](https://www.receiptfaker.com/generate/Maverik-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|BARCODE\|DATE` | 2 | 0.2% | [Mechanic-Receipt](https://www.receiptfaker.com/generate/Mechanic-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|PAYMENT\|CUSTOM` | 2 | 0.2% | [Zaxby's-US-Receipt](https://www.receiptfaker.com/generate/Zaxby's-US-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Meijer-Receipt](https://www.receiptfaker.com/generate/Meijer-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE` | 2 | 0.2% | [Mie-Gacoan-Receipt](https://www.receiptfaker.com/generate/Mie-Gacoan-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|BARCODE` | 2 | 0.2% | [Neiman-Marcus-Receipt](https://www.receiptfaker.com/generate/Neiman-Marcus-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 2 | 0.2% | [Papa-John's-Receipt](https://www.receiptfaker.com/generate/Papa-John's-Receipt) |
| `HEADER\|HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [PACSUN-Receipt](https://www.receiptfaker.com/generate/PACSUN-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|DATE` | 2 | 0.2% | [Petco-Receipt](https://www.receiptfaker.com/generate/Petco-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 2 | 0.2% | [REWE-Receipt](https://www.receiptfaker.com/generate/REWE-Receipt) |
| `HEADER\|PAYMENT\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [Sheetz-Receipt](https://www.receiptfaker.com/generate/Sheetz-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|DATE\|BARCODE\|CUSTOM` | 2 | 0.2% | [Starbucks-Receipt](https://www.receiptfaker.com/generate/Starbucks-Receipt) |
| `HEADER\|DATE\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM` | 2 | 0.2% | [Stater-Bros.-Receipt](https://www.receiptfaker.com/generate/Stater-Bros.-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|BARCODE` | 2 | 0.2% | [The-O2-Receipt](https://www.receiptfaker.com/generate/The-O2-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 2 | 0.2% | [Vodafone-Receipt](https://www.receiptfaker.com/generate/Vodafone-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|DATE\|ITEMS\|CUSTOM\|BARCODE` | 2 | 0.2% | [Zaxby's-Receipt](https://www.receiptfaker.com/generate/Zaxby's-Receipt) |
| `HEADER\|CUSTOM\|DATE\|CUSTOM\|CUSTOM\|ITEMS\|BARCODE` | 1 | 0.1% | [501(c)(3)-Donation-Receipt](https://www.receiptfaker.com/generate/501(c)(3)-Donation-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [7-Eleven-Receipt](https://www.receiptfaker.com/generate/7-Eleven-Receipt) |
| `HEADER\|DATE\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [ACME-Grocery-Receipt](https://www.receiptfaker.com/generate/ACME-Grocery-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [AEON-Receipt](https://www.receiptfaker.com/generate/AEON-Receipt) |
| `HEADER\|ITEMS\|DATE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [ALDI-Receipt](https://www.receiptfaker.com/generate/ALDI-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|DATE` | 1 | 0.1% | [ARCO-Receipt](https://www.receiptfaker.com/generate/ARCO-Receipt) |
| `CUSTOM\|CUSTOM\|HEADER\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [ASDA-Store-Receipt](https://www.receiptfaker.com/generate/ASDA-Store-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|ITEMS\|CUSTOM` | 1 | 0.1% | [AandW-Fast-Food-Receipt](https://www.receiptfaker.com/generate/AandW-Fast-Food-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE` | 1 | 0.1% | [Action-Receipt](https://www.receiptfaker.com/generate/Action-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Adidas-Receipt](https://www.receiptfaker.com/generate/Adidas-Receipt) |
| `HEADER\|CUSTOM\|DATE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 1 | 0.1% | [Airport-Parking-Receipt](https://www.receiptfaker.com/generate/Airport-Parking-Receipt) |
| `HEADER\|DATE\|CUSTOM\|ITEMS\|CUSTOM\|PAYMENT` | 1 | 0.1% | [Airport-Taxi-Receipt](https://www.receiptfaker.com/generate/Airport-Taxi-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|BARCODE\|CUSTOM` | 1 | 0.1% | [Alcampo-Spain-Receipt](https://www.receiptfaker.com/generate/Alcampo-Spain-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|BARCODE` | 1 | 0.1% | [Atlantic-Superstore-Receipt](https://www.receiptfaker.com/generate/Atlantic-Superstore-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Auntie-Anne's-Receipt](https://www.receiptfaker.com/generate/Auntie-Anne's-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM\|DATE` | 1 | 0.1% | [Auto-Repair-Receipt](https://www.receiptfaker.com/generate/Auto-Repair-Receipt) |
| `HEADER\|DATE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 1 | 0.1% | [Autozone-Receipt](https://www.receiptfaker.com/generate/Autozone-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Bahama-Breeze-Receipt](https://www.receiptfaker.com/generate/Bahama-Breeze-Receipt) |
| `HEADER\|PAYMENT\|PAYMENT\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Baja-Fresh-Receipt](https://www.receiptfaker.com/generate/Baja-Fresh-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Baldwinsville-Tops-Receipt](https://www.receiptfaker.com/generate/Baldwinsville-Tops-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [BandQ-Receipt](https://www.receiptfaker.com/generate/BandQ-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|DATE\|BARCODE` | 1 | 0.1% | [Bank-Transaction-Receipt](https://www.receiptfaker.com/generate/Bank-Transaction-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Bar-A-BBQ-Receipt](https://www.receiptfaker.com/generate/Bar-A-BBQ-Receipt) |
| `HEADER\|DATE\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Bath-and-Body-Works-Receipt](https://www.receiptfaker.com/generate/Bath-and-Body-Works-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Bench-Cafe-and-Restaurant-Tax-Invoice](https://www.receiptfaker.com/generate/Bench-Cafe-and-Restaurant-Tax-Invoice) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|DATE\|CUSTOM\|BARCODE` | 1 | 0.1% | [Best-Buy-Receipt-example-with-HP-Latitude-Laptop-and-1-more-item-totalling-800-dollars-80-cents](https://www.receiptfaker.com/generate/Best-Buy-Receipt-example-with-HP-Latitude-Laptop-and-1-more-item-totalling-800-dollars-80-cents) |
| `HEADER\|BARCODE\|CUSTOM\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Best-Buy-Sales-Receipt](https://www.receiptfaker.com/generate/Best-Buy-Sales-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [BevMo!-Receipt](https://www.receiptfaker.com/generate/BevMo!-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|BARCODE\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Biedronka-Receipt](https://www.receiptfaker.com/generate/Biedronka-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Billa-Receipt](https://www.receiptfaker.com/generate/Billa-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|PAYMENT\|PAYMENT` | 1 | 0.1% | [Bit's-n-Bob's-Receipt](https://www.receiptfaker.com/generate/Bit's-n-Bob's-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Bojangles-Receipt](https://www.receiptfaker.com/generate/Bojangles-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Bollywood-Parks-Dubai-Receipt](https://www.receiptfaker.com/generate/Bollywood-Parks-Dubai-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Bon-Bini-Supermarket-Receipt](https://www.receiptfaker.com/generate/Bon-Bini-Supermarket-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|RESTAURANT\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Bonefish-Grill-Receipt](https://www.receiptfaker.com/generate/Bonefish-Grill-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|BARCODE\|CUSTOM` | 1 | 0.1% | [Boulangerie-Patisserie-Sicard-Receipt](https://www.receiptfaker.com/generate/Boulangerie-Patisserie-Sicard-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|PAYMENT\|PAYMENT\|CUSTOM\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Brew-Cafe-Receipt](https://www.receiptfaker.com/generate/Brew-Cafe-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Brioche-Doree-Receipt](https://www.receiptfaker.com/generate/Brioche-Doree-Receipt) |
| `HEADER\|PAYMENT\|CUSTOM\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Bristol-Farms-Receipt](https://www.receiptfaker.com/generate/Bristol-Farms-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|PAYMENT\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Brooklyn-Deli-and-Market-Receipt](https://www.receiptfaker.com/generate/Brooklyn-Deli-and-Market-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Brookshire's-Receipt](https://www.receiptfaker.com/generate/Brookshire's-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Burlington-Receipt](https://www.receiptfaker.com/generate/Burlington-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [CARQUEST-Logo-Receipt](https://www.receiptfaker.com/generate/CARQUEST-Logo-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|DATE` | 1 | 0.1% | [CVS-Pharmacy-Receipt-example-with-Cleaning-Wipes-and-1-more-item-totalling-9-dollars-71-cents](https://www.receiptfaker.com/generate/CVS-Pharmacy-Receipt-example-with-Cleaning-Wipes-and-1-more-item-totalling-9-dollars-71-cents) |
| `HEADER\|DATE\|ITEMS\|CUSTOM\|BARCODE\|PAYMENT` | 1 | 0.1% | [CVS-Pharmacy-Receipt-example-with-Pepto-Child-Tabs-Sprite-and-2-more-items-totalling-13-dollars-78-cents](https://www.receiptfaker.com/generate/CVS-Pharmacy-Receipt-example-with-Pepto-Child-Tabs-Sprite-and-2-more-items-totalling-13-dollars-78-cents) |
| `HEADER\|CUSTOM\|ITEMS\|DATE\|CUSTOM` | 1 | 0.1% | [CVS-Pharmacy-Receipt-example-with-Prescription-and-1-more-item-totalling-66-dollars-76-cents](https://www.receiptfaker.com/generate/CVS-Pharmacy-Receipt-example-with-Prescription-and-1-more-item-totalling-66-dollars-76-cents) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Cafe-Rouge-Receipt](https://www.receiptfaker.com/generate/Cafe-Rouge-Receipt) |
| `HEADER\|CUSTOM\|DATE\|CUSTOM\|RESTAURANT\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 1 | 0.1% | [Car-Rental-Receipt](https://www.receiptfaker.com/generate/Car-Rental-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Carl's-Jr.-Receipt](https://www.receiptfaker.com/generate/Carl's-Jr.-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|DATE\|CUSTOM\|BARCODE` | 1 | 0.1% | [Carrefour-Receipt](https://www.receiptfaker.com/generate/Carrefour-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE` | 1 | 0.1% | [Cartier-Receipt](https://www.receiptfaker.com/generate/Cartier-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE\|DATE\|CUSTOM` | 1 | 0.1% | [Cash-Register-Receipt](https://www.receiptfaker.com/generate/Cash-Register-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|HEADER\|CUSTOM` | 1 | 0.1% | [Catherine's-Cafe-To-Go-Receipt](https://www.receiptfaker.com/generate/Catherine's-Cafe-To-Go-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|PAYMENT\|PAYMENT\|PAYMENT` | 1 | 0.1% | [Ceres-Receipt](https://www.receiptfaker.com/generate/Ceres-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|DATE\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Champs-Sports-Receipt](https://www.receiptfaker.com/generate/Champs-Sports-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE` | 1 | 0.1% | [Cheaney-Receipt](https://www.receiptfaker.com/generate/Cheaney-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|DATE` | 1 | 0.1% | [Checkers-Receipt](https://www.receiptfaker.com/generate/Checkers-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|BARCODE\|CUSTOM` | 1 | 0.1% | [Chemist-Warehouse-Receipt](https://www.receiptfaker.com/generate/Chemist-Warehouse-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Chevron-Gas-Station-Receipt](https://www.receiptfaker.com/generate/Chevron-Gas-Station-Receipt) |
| `HEADER\|DATE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Chevron-Receipt](https://www.receiptfaker.com/generate/Chevron-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Chez-Marco-Receipt](https://www.receiptfaker.com/generate/Chez-Marco-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Chico's-Mexican-Food-Receipt](https://www.receiptfaker.com/generate/Chico's-Mexican-Food-Receipt) |
| `HEADER\|CUSTOM\|DATE\|ITEMS\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Chipotle-Receipt](https://www.receiptfaker.com/generate/Chipotle-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Chuck-E.-Cheese-Play-Pass-Receipt](https://www.receiptfaker.com/generate/Chuck-E.-Cheese-Play-Pass-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|ITEMS\|PAYMENT\|CUSTOM\|DATE` | 1 | 0.1% | [Cleaning-Receipt](https://www.receiptfaker.com/generate/Cleaning-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Coles-Express-Receipt](https://www.receiptfaker.com/generate/Coles-Express-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Conrad-Centennial-Singapore-Receipt](https://www.receiptfaker.com/generate/Conrad-Centennial-Singapore-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Construction-Receipt](https://www.receiptfaker.com/generate/Construction-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|DATE\|BARCODE\|CUSTOM\|CUSTOM\|DATE` | 1 | 0.1% | [Costco-Receipt](https://www.receiptfaker.com/generate/Costco-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|BARCODE` | 1 | 0.1% | [Country-Hills-Market-Receipt](https://www.receiptfaker.com/generate/Country-Hills-Market-Receipt) |
| `BARCODE\|CUSTOM\|HEADER\|CUSTOM\|DATE\|ITEMS\|CUSTOM` | 1 | 0.1% | [Cracker-Barrel-Receipt](https://www.receiptfaker.com/generate/Cracker-Barrel-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Cream-Stone-Receipt](https://www.receiptfaker.com/generate/Cream-Stone-Receipt) |
| `DATE\|HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM` | 1 | 0.1% | [Credit-Card-Receipt](https://www.receiptfaker.com/generate/Credit-Card-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS` | 1 | 0.1% | [Cub-Receipt](https://www.receiptfaker.com/generate/Cub-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|PAYMENT\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Cumberland-Farms-Receipt](https://www.receiptfaker.com/generate/Cumberland-Farms-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Currys-PC-World-Receipt](https://www.receiptfaker.com/generate/Currys-PC-World-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|PAYMENT` | 1 | 0.1% | [DICK'S-Receipt](https://www.receiptfaker.com/generate/DICK'S-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|BARCODE\|ITEMS` | 1 | 0.1% | [Dealz-Receipt](https://www.receiptfaker.com/generate/Dealz-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Del-Taco-Receipt](https://www.receiptfaker.com/generate/Del-Taco-Receipt) |
| `HEADER\|DATE\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE` | 1 | 0.1% | [Dick's-Sporting-Goods-Receipt](https://www.receiptfaker.com/generate/Dick's-Sporting-Goods-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Dillons-Receipt](https://www.receiptfaker.com/generate/Dillons-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Dollar-General-Receipt](https://www.receiptfaker.com/generate/Dollar-General-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS` | 1 | 0.1% | [Domino's-Pizza-Receipt](https://www.receiptfaker.com/generate/Domino's-Pizza-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE` | 1 | 0.1% | [Donation-Receipt](https://www.receiptfaker.com/generate/Donation-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Dunelm-Receipt](https://www.receiptfaker.com/generate/Dunelm-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|CUSTOM\|PAYMENT\|CUSTOM` | 1 | 0.1% | [ESTG-Grill-and-Bistro-Receipt](https://www.receiptfaker.com/generate/ESTG-Grill-and-Bistro-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Einstein-Bros-Bagels-Receipt](https://www.receiptfaker.com/generate/Einstein-Bros-Bagels-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|PAYMENT\|BARCODE` | 1 | 0.1% | [El-Pollo-Loco-Receipt](https://www.receiptfaker.com/generate/El-Pollo-Loco-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Electrician-Receipt](https://www.receiptfaker.com/generate/Electrician-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|DATE` | 1 | 0.1% | [Equipment-Rental-Receipt](https://www.receiptfaker.com/generate/Equipment-Rental-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Eurospin-Italy-Receipt](https://www.receiptfaker.com/generate/Eurospin-Italy-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Family-Dollar-Receipt](https://www.receiptfaker.com/generate/Family-Dollar-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|PAYMENT\|PAYMENT\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [FarmSudz-Receipt](https://www.receiptfaker.com/generate/FarmSudz-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS` | 1 | 0.1% | [Farmavalue-Receipt](https://www.receiptfaker.com/generate/Farmavalue-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Fastenal-Receipt](https://www.receiptfaker.com/generate/Fastenal-Receipt) |
| `HEADER\|PAYMENT\|CUSTOM\|PAYMENT` | 1 | 0.1% | [Fastop-Receipt](https://www.receiptfaker.com/generate/Fastop-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Festival-Foods-Receipt](https://www.receiptfaker.com/generate/Festival-Foods-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Flanigan's-Seafood-Bar-and-Grill-Receipt](https://www.receiptfaker.com/generate/Flanigan's-Seafood-Bar-and-Grill-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 1 | 0.1% | [Food-Delivery-Receipt](https://www.receiptfaker.com/generate/Food-Delivery-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|DATE\|BARCODE\|CUSTOM` | 1 | 0.1% | [Food-Lion-Receipt](https://www.receiptfaker.com/generate/Food-Lion-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|ITEMS` | 1 | 0.1% | [FoodMaxx-Receipt](https://www.receiptfaker.com/generate/FoodMaxx-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Foster's-Hollywood-Receipt](https://www.receiptfaker.com/generate/Foster's-Hollywood-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|PAYMENT\|CUSTOM\|PAYMENT` | 1 | 0.1% | [Four-Seasons-Siam-Paragon-Receipt](https://www.receiptfaker.com/generate/Four-Seasons-Siam-Paragon-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Freddy's-Frozen-Custard-and-Steakburgers-Receipt](https://www.receiptfaker.com/generate/Freddy's-Frozen-Custard-and-Steakburgers-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [FreshCo-Receipt](https://www.receiptfaker.com/generate/FreshCo-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM\|DATE` | 1 | 0.1% | [Funeral-Receipt](https://www.receiptfaker.com/generate/Funeral-Receipt) |
| `HEADER\|DATE\|BARCODE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [GAP-Receipt](https://www.receiptfaker.com/generate/GAP-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|ITEMS` | 1 | 0.1% | [GBK-Cribbs-Causeway-Receipt](https://www.receiptfaker.com/generate/GBK-Cribbs-Causeway-Receipt) |
| `HEADER\|CUSTOM\|DATE\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Generic-Business-Receipt](https://www.receiptfaker.com/generate/Generic-Business-Receipt) |
| `HEADER\|DATE\|CUSTOM\|RESTAURANT\|RESTAURANT\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 1 | 0.1% | [Generic-POS-Receipt](https://www.receiptfaker.com/generate/Generic-POS-Receipt) |
| `DATE\|HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Generic-Parking-Receipt](https://www.receiptfaker.com/generate/Generic-Parking-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|BARCODE\|PAYMENT\|CUSTOM\|DATE` | 1 | 0.1% | [Generic-Service-Receipt](https://www.receiptfaker.com/generate/Generic-Service-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE` | 1 | 0.1% | [Golden-Corral-Receipt](https://www.receiptfaker.com/generate/Golden-Corral-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Gordon-Ramsay-Plane-Food-Receipt](https://www.receiptfaker.com/generate/Gordon-Ramsay-Plane-Food-Receipt) |
| `HEADER\|DATE\|RESTAURANT\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Goyard-Boutique-Receipt](https://www.receiptfaker.com/generate/Goyard-Boutique-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Granger-and-Co.-Receipt](https://www.receiptfaker.com/generate/Granger-and-Co.-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Guld-and-Rod-Receipt](https://www.receiptfaker.com/generate/Guld-and-Rod-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [H-Mart-Receipt](https://www.receiptfaker.com/generate/H-Mart-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Hai-Lan-Coffee-Receipt](https://www.receiptfaker.com/generate/Hai-Lan-Coffee-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Half-Price-Books-Receipt](https://www.receiptfaker.com/generate/Half-Price-Books-Receipt) |
| `CUSTOM\|HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM` | 1 | 0.1% | [Harbor-Freight-Tools-Receipt](https://www.receiptfaker.com/generate/Harbor-Freight-Tools-Receipt) |
| `HEADER\|RESTAURANT\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM\|DATE` | 1 | 0.1% | [Hardee's-Receipt](https://www.receiptfaker.com/generate/Hardee's-Receipt) |
| `HEADER\|PAYMENT\|CUSTOM\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Hardee's-of-Dickinson-Receipt](https://www.receiptfaker.com/generate/Hardee's-of-Dickinson-Receipt) |
| `CUSTOM\|HEADER\|CUSTOM\|CUSTOM\|DATE\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Hartford-Baking-Co.-Receipt](https://www.receiptfaker.com/generate/Hartford-Baking-Co.-Receipt) |
| `CUSTOM\|HEADER\|CUSTOM\|RESTAURANT\|ITEMS\|CUSTOM\|DATE` | 1 | 0.1% | [Hawaiian-Bros-Island-Grill-Receipt](https://www.receiptfaker.com/generate/Hawaiian-Bros-Island-Grill-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [HeHa-Waterfall-Receipt](https://www.receiptfaker.com/generate/HeHa-Waterfall-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|BARCODE\|CUSTOM` | 1 | 0.1% | [Helzberg-Diamonds-Receipt](https://www.receiptfaker.com/generate/Helzberg-Diamonds-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|DATE\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Hilton-Hotel-Receipt](https://www.receiptfaker.com/generate/Hilton-Hotel-Receipt) |
| `HEADER\|DATE\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM` | 1 | 0.1% | [Holiday-Inn-Receipt](https://www.receiptfaker.com/generate/Holiday-Inn-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Home-Depot-Retail-Receipt](https://www.receiptfaker.com/generate/Home-Depot-Retail-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|PAYMENT\|DATE` | 1 | 0.1% | [Homebase-Receipt](https://www.receiptfaker.com/generate/Homebase-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Humble-Origins-Coffee-Roasters-Receipt](https://www.receiptfaker.com/generate/Humble-Origins-Coffee-Roasters-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Hungry-Horse-Receipt](https://www.receiptfaker.com/generate/Hungry-Horse-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [ISABEL-MARANT-Receipt](https://www.receiptfaker.com/generate/ISABEL-MARANT-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|RESTAURANT\|ITEMS\|ITEMS\|BARCODE\|CUSTOM` | 1 | 0.1% | [Iceland-Store-Receipt](https://www.receiptfaker.com/generate/Iceland-Store-Receipt) |
| `HEADER\|DATE\|DATE\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Indian-Petrol-Pump-Receipt](https://www.receiptfaker.com/generate/Indian-Petrol-Pump-Receipt) |
| `HEADER\|BARCODE\|DATE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Indian-Restaurant-Bill](https://www.receiptfaker.com/generate/Indian-Restaurant-Bill) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Itemized-Sales-Receipt](https://www.receiptfaker.com/generate/Itemized-Sales-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Itsu-Receipt](https://www.receiptfaker.com/generate/Itsu-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [J.CO-Pluit-Village-Receipt](https://www.receiptfaker.com/generate/J.CO-Pluit-Village-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [J.Crew-Receipt](https://www.receiptfaker.com/generate/J.Crew-Receipt) |
| `HEADER\|CUSTOM\|DATE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [JOZY-Receipt](https://www.receiptfaker.com/generate/JOZY-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS` | 1 | 0.1% | [JW-Marriott-Receipt](https://www.receiptfaker.com/generate/JW-Marriott-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|BARCODE` | 1 | 0.1% | [JYSK-Receipt](https://www.receiptfaker.com/generate/JYSK-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Jamba-Receipt](https://www.receiptfaker.com/generate/Jamba-Receipt) |
| `HEADER\|CUSTOM\|RESTAURANT\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Jay-Jays-Receipt](https://www.receiptfaker.com/generate/Jay-Jays-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS` | 1 | 0.1% | [Jhoots-Pharmacy-Receipt](https://www.receiptfaker.com/generate/Jhoots-Pharmacy-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|DATE` | 1 | 0.1% | [Joe's-Kansas-City-Bar-B-Que-Receipt](https://www.receiptfaker.com/generate/Joe's-Kansas-City-Bar-B-Que-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|BARCODE\|CUSTOM` | 1 | 0.1% | [John-Lewis-Concession-Receipt](https://www.receiptfaker.com/generate/John-Lewis-Concession-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Jollibee-Receipt](https://www.receiptfaker.com/generate/Jollibee-Receipt) |
| `HEADER\|DATE\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Journeys-Receipt](https://www.receiptfaker.com/generate/Journeys-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|CUSTOM\|DATE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [King-Soopers-Receipt](https://www.receiptfaker.com/generate/King-Soopers-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|ITEMS\|DATE\|CUSTOM\|BARCODE` | 1 | 0.1% | [Kroger-Receipt-example-with-Google-Play-Card-for-200-dollars](https://www.receiptfaker.com/generate/Kroger-Receipt-example-with-Google-Play-Card-for-200-dollars) |
| `HEADER\|PAYMENT\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Krystal-LaFollette-Receipt](https://www.receiptfaker.com/generate/Krystal-LaFollette-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [LIDL-Receipt](https://www.receiptfaker.com/generate/LIDL-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [La-Rotonde-Receipt](https://www.receiptfaker.com/generate/La-Rotonde-Receipt) |
| `HEADER\|CUSTOM\|DATE\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM` | 1 | 0.1% | [Labor-Receipt](https://www.receiptfaker.com/generate/Labor-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|DATE` | 1 | 0.1% | [Locksmith-Receipt](https://www.receiptfaker.com/generate/Locksmith-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|ITEMS` | 1 | 0.1% | [Love's-Travel-Stop-Receipt](https://www.receiptfaker.com/generate/Love's-Travel-Stop-Receipt) |
| `CUSTOM\|HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Lynn-Valley-AandW-Receipt](https://www.receiptfaker.com/generate/Lynn-Valley-AandW-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [MIDAS-Shoes-Receipt](https://www.receiptfaker.com/generate/MIDAS-Shoes-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Macy's-Receipt](https://www.receiptfaker.com/generate/Macy's-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Mama-Joyce's-Soul-Food-Receipt](https://www.receiptfaker.com/generate/Mama-Joyce's-Soul-Food-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Mariano's-Receipt](https://www.receiptfaker.com/generate/Mariano's-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Marigold-Restaurant-Receipt](https://www.receiptfaker.com/generate/Marigold-Restaurant-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Marshalls-Receipt](https://www.receiptfaker.com/generate/Marshalls-Receipt) |
| `HEADER\|ITEMS\|HEADER\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Martinho-Optica-(Ourivesaria)-Receipt](https://www.receiptfaker.com/generate/Martinho-Optica-(Ourivesaria)-Receipt) |
| `CUSTOM\|HEADER\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Masters-Receipt](https://www.receiptfaker.com/generate/Masters-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|HEADER` | 1 | 0.1% | [Matjeom-Central-Market-Receipt](https://www.receiptfaker.com/generate/Matjeom-Central-Market-Receipt) |
| `HEADER\|DATE\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Mazzio's-Receipt](https://www.receiptfaker.com/generate/Mazzio's-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE\|CUSTOM\|CUSTOM\|DATE` | 1 | 0.1% | [Mechanic-Shop-Receipt](https://www.receiptfaker.com/generate/Mechanic-Shop-Receipt) |
| `HEADER\|CUSTOM\|DATE\|ITEMS\|BARCODE\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Medicine-Receipt](https://www.receiptfaker.com/generate/Medicine-Receipt) |
| `HEADER\|DATE\|ITEMS\|BARCODE` | 1 | 0.1% | [Mediterraneo-Cucina-Italiana-Receipt](https://www.receiptfaker.com/generate/Mediterraneo-Cucina-Italiana-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Menards-Receipt](https://www.receiptfaker.com/generate/Menards-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Mentone-BCF-Receipt](https://www.receiptfaker.com/generate/Mentone-BCF-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Mercadona-Delivery-Receipt](https://www.receiptfaker.com/generate/Mercadona-Delivery-Receipt) |
| `HEADER\|BARCODE\|ITEMS\|CUSTOM` | 1 | 0.1% | [Mercadona-Spain-Receipt](https://www.receiptfaker.com/generate/Mercadona-Spain-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Metro-Receipt](https://www.receiptfaker.com/generate/Metro-Receipt) |
| `HEADER\|PAYMENT\|CUSTOM\|PAYMENT\|PAYMENT\|PAYMENT\|BARCODE\|CUSTOM` | 1 | 0.1% | [Metropolitan-Market-Receipt](https://www.receiptfaker.com/generate/Metropolitan-Market-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS` | 1 | 0.1% | [Mexico-Lindo-Mexican-Restaurant-Receipt](https://www.receiptfaker.com/generate/Mexico-Lindo-Mexican-Restaurant-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Michael-Chell-Receipt](https://www.receiptfaker.com/generate/Michael-Chell-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Michaels-Receipt](https://www.receiptfaker.com/generate/Michaels-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Moe's-Southwest-Grill-Receipt](https://www.receiptfaker.com/generate/Moe's-Southwest-Grill-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Mojito-Receipt](https://www.receiptfaker.com/generate/Mojito-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|DATE\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Monthly-Parking-Receipt](https://www.receiptfaker.com/generate/Monthly-Parking-Receipt) |
| `HEADER\|RESTAURANT\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Morrisons-Cafe-Receipt](https://www.receiptfaker.com/generate/Morrisons-Cafe-Receipt) |
| `HEADER\|CUSTOM\|DATE\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 1 | 0.1% | [Motel-Receipt](https://www.receiptfaker.com/generate/Motel-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|PAYMENT\|ITEMS\|CUSTOM` | 1 | 0.1% | [Moxies-Restaurant-Receipt](https://www.receiptfaker.com/generate/Moxies-Restaurant-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [NAPA-Auto-Parts-Receipt](https://www.receiptfaker.com/generate/NAPA-Auto-Parts-Receipt) |
| `HEADER\|CUSTOM\|DATE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [NYC-Taxi-Receipt](https://www.receiptfaker.com/generate/NYC-Taxi-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Noel-Leeming-Receipt](https://www.receiptfaker.com/generate/Noel-Leeming-Receipt) |
| `CUSTOM\|HEADER\|CUSTOM\|PAYMENT\|ITEMS\|CUSTOM` | 1 | 0.1% | [Noodles-Kober-Receipt](https://www.receiptfaker.com/generate/Noodles-Kober-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|BARCODE\|CUSTOM` | 1 | 0.1% | [Nordstrom-Store-Receipt](https://www.receiptfaker.com/generate/Nordstrom-Store-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [ORLEN-Receipt](https://www.receiptfaker.com/generate/ORLEN-Receipt) |
| `HEADER\|PAYMENT\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Odettes-Eatery-Receipt](https://www.receiptfaker.com/generate/Odettes-Eatery-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Office-Depot-OfficeMax-Receipt](https://www.receiptfaker.com/generate/Office-Depot-OfficeMax-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Oil-Change-Receipt](https://www.receiptfaker.com/generate/Oil-Change-Receipt) |
| `DATE\|HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Ola-Cab-Receipt](https://www.receiptfaker.com/generate/Ola-Cab-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|BARCODE` | 1 | 0.1% | [PIGI-Pasta-Bar-Receipt](https://www.receiptfaker.com/generate/PIGI-Pasta-Bar-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|CUSTOM\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Pappasito's-Cantina-Receipt](https://www.receiptfaker.com/generate/Pappasito's-Cantina-Receipt) |
| `HEADER\|DATE\|RESTAURANT\|ITEMS\|CUSTOM` | 1 | 0.1% | [Parking-lot-receipt](https://www.receiptfaker.com/generate/Parking-lot-receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Party-King-Receipt](https://www.receiptfaker.com/generate/Party-King-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Pavilions-Receipt](https://www.receiptfaker.com/generate/Pavilions-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Perkins-Restaurant-and-Bakery-Receipt](https://www.receiptfaker.com/generate/Perkins-Restaurant-and-Bakery-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|DATE` | 1 | 0.1% | [Petrol-Receipt](https://www.receiptfaker.com/generate/Petrol-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Pilot-Receipt](https://www.receiptfaker.com/generate/Pilot-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|RESTAURANT\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Pizza-Hut-Receipt](https://www.receiptfaker.com/generate/Pizza-Hut-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Plumbing-Receipt](https://www.receiptfaker.com/generate/Plumbing-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Pokusevskis-Receipt](https://www.receiptfaker.com/generate/Pokusevskis-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|ITEMS` | 1 | 0.1% | [Popeyes-Receipt](https://www.receiptfaker.com/generate/Popeyes-Receipt) |
| `HEADER\|PAYMENT\|CUSTOM\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Portillo's-Receipt](https://www.receiptfaker.com/generate/Portillo's-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Post-Office-Ltd-Self-Service-Receipt](https://www.receiptfaker.com/generate/Post-Office-Ltd-Self-Service-Receipt) |
| `HEADER\|RESTAURANT\|ITEMS\|DATE\|CUSTOM\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Prada-Receipt](https://www.receiptfaker.com/generate/Prada-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|DATE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Prescription-Receipt](https://www.receiptfaker.com/generate/Prescription-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Primark-Rotterdam-Receipt](https://www.receiptfaker.com/generate/Primark-Rotterdam-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|CUSTOM\|DATE` | 1 | 0.1% | [Publix-Receipt](https://www.receiptfaker.com/generate/Publix-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [REI-Co-op-Receipt](https://www.receiptfaker.com/generate/REI-Co-op-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [ROSS-Dress-For-Less-Receipt](https://www.receiptfaker.com/generate/ROSS-Dress-For-Less-Receipt) |
| `HEADER\|ITEMS\|ITEMS` | 1 | 0.1% | [RaceTrac-Receipt](https://www.receiptfaker.com/generate/RaceTrac-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Raley's-Receipt](https://www.receiptfaker.com/generate/Raley's-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|CUSTOM\|DATE\|CUSTOM` | 1 | 0.1% | [Ralphs-Receipt](https://www.receiptfaker.com/generate/Ralphs-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|HEADER` | 1 | 0.1% | [Razz-Coffee-Receipt](https://www.receiptfaker.com/generate/Razz-Coffee-Receipt) |
| `HEADER\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Real-Canadian-Superstore-Receipt](https://www.receiptfaker.com/generate/Real-Canadian-Superstore-Receipt) |
| `CUSTOM\|ITEMS\|PAYMENT\|BARCODE` | 1 | 0.1% | [Receipt-example-with-Google-Play-and-2-more-items-totalling-dollar75.00](https://www.receiptfaker.com/generate/Receipt-example-with-Google-Play-and-2-more-items-totalling-dollar75.00) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Red-Lobster-Receipt](https://www.receiptfaker.com/generate/Red-Lobster-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Red-Robin-Receipt](https://www.receiptfaker.com/generate/Red-Robin-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|BARCODE\|CUSTOM` | 1 | 0.1% | [Regalado-Market-Receipt](https://www.receiptfaker.com/generate/Regalado-Market-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|DATE\|BARCODE` | 1 | 0.1% | [Rent-Payment-Receipt](https://www.receiptfaker.com/generate/Rent-Payment-Receipt) |
| `HEADER\|PAYMENT\|PAYMENT\|CUSTOM\|PAYMENT` | 1 | 0.1% | [Restauracja-Atmosfera-Receipt](https://www.receiptfaker.com/generate/Restauracja-Atmosfera-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [River-Island-Receipt](https://www.receiptfaker.com/generate/River-Island-Receipt) |
| `HEADER\|DATE\|BARCODE\|ITEMS\|PAYMENT` | 1 | 0.1% | [Rolex-receipt-example-with-Oyster-Perpetual-and-1-more-item-totalling-104-dollars-55-cents](https://www.receiptfaker.com/generate/Rolex-receipt-example-with-Oyster-Perpetual-and-1-more-item-totalling-104-dollars-55-cents) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Royal-Mail-Receipt](https://www.receiptfaker.com/generate/Royal-Mail-Receipt) |
| `HEADER\|PAYMENT\|PAYMENT\|PAYMENT\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Rubio's-Receipt](https://www.receiptfaker.com/generate/Rubio's-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [SMYK-Receipt](https://www.receiptfaker.com/generate/SMYK-Receipt) |
| `HEADER\|HEADER\|DATE\|ITEMS\|PAYMENT` | 1 | 0.1% | [SONO-Japanese-Restaurant-Receipt](https://www.receiptfaker.com/generate/SONO-Japanese-Restaurant-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [SS-Fried-Chicken-Lhokseumawe-Receipt](https://www.receiptfaker.com/generate/SS-Fried-Chicken-Lhokseumawe-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|PAYMENT\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Sainsbury's-Receipt](https://www.receiptfaker.com/generate/Sainsbury's-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|HEADER` | 1 | 0.1% | [Saint-Laurent-Paris-Receipt](https://www.receiptfaker.com/generate/Saint-Laurent-Paris-Receipt) |
| `HEADER\|DATE\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE` | 1 | 0.1% | [Salem-Pharmacy-Receipt](https://www.receiptfaker.com/generate/Salem-Pharmacy-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Sally-Beauty-Receipt](https://www.receiptfaker.com/generate/Sally-Beauty-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|DATE\|DATE\|BARCODE\|CUSTOM` | 1 | 0.1% | [Sam's-Club-Receipt](https://www.receiptfaker.com/generate/Sam's-Club-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [San-Carlo-Receipt](https://www.receiptfaker.com/generate/San-Carlo-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS` | 1 | 0.1% | [Schlotzsky's-Receipt](https://www.receiptfaker.com/generate/Schlotzsky's-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Screwfix-Invoice-Receipt](https://www.receiptfaker.com/generate/Screwfix-Invoice-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS` | 1 | 0.1% | [Seafood-City-Receipt](https://www.receiptfaker.com/generate/Seafood-City-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|ITEMS` | 1 | 0.1% | [Seasons-52-Receipt](https://www.receiptfaker.com/generate/Seasons-52-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Selfridges-Receipt](https://www.receiptfaker.com/generate/Selfridges-Receipt) |
| `HEADER\|CUSTOM\|DATE\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Shake-Shack-Receipt](https://www.receiptfaker.com/generate/Shake-Shack-Receipt) |
| `HEADER\|PAYMENT\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Shake-Shack-Singapore-Receipt](https://www.receiptfaker.com/generate/Shake-Shack-Singapore-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|ITEMS` | 1 | 0.1% | [Shoney's-Receipt](https://www.receiptfaker.com/generate/Shoney's-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Shoppers-Drug-Mart-Receipt](https://www.receiptfaker.com/generate/Shoppers-Drug-Mart-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Shoprite-Receipt](https://www.receiptfaker.com/generate/Shoprite-Receipt) |
| `CUSTOM\|DATE\|HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Simple-Business-Receipt](https://www.receiptfaker.com/generate/Simple-Business-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Skechers-Receipt](https://www.receiptfaker.com/generate/Skechers-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|BARCODE\|DATE` | 1 | 0.1% | [Smart-and-Final-Receipt](https://www.receiptfaker.com/generate/Smart-and-Final-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS` | 1 | 0.1% | [Sobeys-Receipt](https://www.receiptfaker.com/generate/Sobeys-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS` | 1 | 0.1% | [Soloman-Cutler-Receipt](https://www.receiptfaker.com/generate/Soloman-Cutler-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|BARCODE\|DATE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Splend'Or-Receipt](https://www.receiptfaker.com/generate/Splend'Or-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|BARCODE\|CUSTOM` | 1 | 0.1% | [Sports-Direct-Receipt](https://www.receiptfaker.com/generate/Sports-Direct-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT` | 1 | 0.1% | [Square-POS-Receipt](https://www.receiptfaker.com/generate/Square-POS-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Staples-Receipt](https://www.receiptfaker.com/generate/Staples-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|PAYMENT\|CUSTOM` | 1 | 0.1% | [State-and-Main-Kitchen-+-Bar-Receipt](https://www.receiptfaker.com/generate/State-and-Main-Kitchen-+-Bar-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Steak-'n-Shake-Receipt](https://www.receiptfaker.com/generate/Steak-'n-Shake-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [StockX-Receipt](https://www.receiptfaker.com/generate/StockX-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE\|DATE` | 1 | 0.1% | [Summer-Camp-Receipt](https://www.receiptfaker.com/generate/Summer-Camp-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|PAYMENT\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Sunglass-Hut-Receipt](https://www.receiptfaker.com/generate/Sunglass-Hut-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|PAYMENT\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Super-Food-Aruba-Receipt](https://www.receiptfaker.com/generate/Super-Food-Aruba-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|RESTAURANT\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Swiggy-Receipt](https://www.receiptfaker.com/generate/Swiggy-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|DATE` | 1 | 0.1% | [T-Mobile-Receipt](https://www.receiptfaker.com/generate/T-Mobile-Receipt) |
| `HEADER\|HEADER\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [TAB-Gida-Receipt](https://www.receiptfaker.com/generate/TAB-Gida-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|BARCODE\|ITEMS\|CUSTOM\|PAYMENT\|PAYMENT\|ITEMS` | 1 | 0.1% | [TELUS-Mobile-Store-Receipt](https://www.receiptfaker.com/generate/TELUS-Mobile-Store-Receipt) |
| `HEADER` | 1 | 0.1% | [THE-PORT-AUTHORITY-Receipt](https://www.receiptfaker.com/generate/THE-PORT-AUTHORITY-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|PAYMENT\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Ta-Wan-Receipt](https://www.receiptfaker.com/generate/Ta-Wan-Receipt) |
| `HEADER\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Taco-John's-Galesburg-Receipt](https://www.receiptfaker.com/generate/Taco-John's-Galesburg-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Tailwind-Concessions-Receipt](https://www.receiptfaker.com/generate/Tailwind-Concessions-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Takko-Fashion-Receipt](https://www.receiptfaker.com/generate/Takko-Fashion-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Target-Receipt-example-with-Lion-Mints-Debit-Card-and-3-more-items-totalling-21-dollars-29-cents](https://www.receiptfaker.com/generate/Target-Receipt-example-with-Lion-Mints-Debit-Card-and-3-more-items-totalling-21-dollars-29-cents) |
| `HEADER\|RESTAURANT\|ITEMS\|DATE\|CUSTOM` | 1 | 0.1% | [Taxi-Ride-Receipt](https://www.receiptfaker.com/generate/Taxi-Ride-Receipt) |
| `HEADER\|CUSTOM\|PAYMENT\|PAYMENT\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Tazik-Receipt](https://www.receiptfaker.com/generate/Tazik-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Tesco-Receipt](https://www.receiptfaker.com/generate/Tesco-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|ITEMS` | 1 | 0.1% | [The-Beefeater-Spain-Receipt](https://www.receiptfaker.com/generate/The-Beefeater-Spain-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|HEADER\|CUSTOM` | 1 | 0.1% | [The-Cheesecake-Factory-Ross-Park-Receipt](https://www.receiptfaker.com/generate/The-Cheesecake-Factory-Ross-Park-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [The-Flower-Shop-Receipt](https://www.receiptfaker.com/generate/The-Flower-Shop-Receipt) |
| `HEADER\|CUSTOM\|RESTAURANT\|ITEMS\|ITEMS` | 1 | 0.1% | [The-Food-Warehouse-Receipt](https://www.receiptfaker.com/generate/The-Food-Warehouse-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|ITEMS` | 1 | 0.1% | [The-Gym-Group-Receipt](https://www.receiptfaker.com/generate/The-Gym-Group-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [The-Kooples-Receipt](https://www.receiptfaker.com/generate/The-Kooples-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|ITEMS` | 1 | 0.1% | [The-Old-Manor-Receipt](https://www.receiptfaker.com/generate/The-Old-Manor-Receipt) |
| `CUSTOM\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [The-Pack-Horse-Receipt](https://www.receiptfaker.com/generate/The-Pack-Horse-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|DATE` | 1 | 0.1% | [Therapy-Receipt](https://www.receiptfaker.com/generate/Therapy-Receipt) |
| `HEADER\|BARCODE\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Tom-Thumb-Receipt](https://www.receiptfaker.com/generate/Tom-Thumb-Receipt) |
| `HEADER\|PAYMENT\|CUSTOM\|CUSTOM\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM` | 1 | 0.1% | [Torchy's-Tacos-Receipt](https://www.receiptfaker.com/generate/Torchy's-Tacos-Receipt) |
| `HEADER\|ITEMS\|DATE\|CUSTOM` | 1 | 0.1% | [Trader-Joe's-Receipt](https://www.receiptfaker.com/generate/Trader-Joe's-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Turtle-Bay-Receipt](https://www.receiptfaker.com/generate/Turtle-Bay-Receipt) |
| `HEADER\|CUSTOM\|DATE\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE` | 1 | 0.1% | [Tutoring-Receipt](https://www.receiptfaker.com/generate/Tutoring-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [UNIQLO-Receipt](https://www.receiptfaker.com/generate/UNIQLO-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [UPS-Shipping-Receipt](https://www.receiptfaker.com/generate/UPS-Shipping-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [USPS-Receipt](https://www.receiptfaker.com/generate/USPS-Receipt) |
| `HEADER\|DATE\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|PAYMENT` | 1 | 0.1% | [Uber-Receipt](https://www.receiptfaker.com/generate/Uber-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [Uncle-Paul's-Pizza-Receipt](https://www.receiptfaker.com/generate/Uncle-Paul's-Pizza-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|BARCODE\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Unieuro-Receipt](https://www.receiptfaker.com/generate/Unieuro-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|BARCODE\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Urban-Outfitters-Receipt](https://www.receiptfaker.com/generate/Urban-Outfitters-Receipt) |
| `HEADER\|CUSTOM\|RESTAURANT\|ITEMS\|DATE\|CUSTOM\|CUSTOM\|CUSTOM\|PAYMENT\|BARCODE\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Valentino-Boutique-Receipt](https://www.receiptfaker.com/generate/Valentino-Boutique-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Vallarta-Supermarkets-Receipt](https://www.receiptfaker.com/generate/Vallarta-Supermarkets-Receipt) |
| `CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Van's-Burgers-Receipt](https://www.receiptfaker.com/generate/Van's-Burgers-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|HEADER\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Veerman-Juwelen-Receipt](https://www.receiptfaker.com/generate/Veerman-Juwelen-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Vege-Mart-Grocery-Receipt](https://www.receiptfaker.com/generate/Vege-Mart-Grocery-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [Verizon-Receipt](https://www.receiptfaker.com/generate/Verizon-Receipt) |
| `HEADER\|DATE\|RESTAURANT\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Victoria's-Secret-Receipt](https://www.receiptfaker.com/generate/Victoria's-Secret-Receipt) |
| `HEADER\|DATE\|CUSTOM\|ITEMS\|PAYMENT\|BARCODE` | 1 | 0.1% | [Visions-Electronics-Receipt](https://www.receiptfaker.com/generate/Visions-Electronics-Receipt) |
| `HEADER\|DATE\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Vons-Receipt-example-with-Broccoli-Cereal-Honey-Oats-Penne-Pasta-Eggs-Chicken-Breast-Toilet-Paper-Tomatoes-Bottled-Water-Orange-Juice-Apples-and-Skyy-Vodka-totalling-58-dollars-81-cents](https://www.receiptfaker.com/generate/Vons-Receipt-example-with-Broccoli-Cereal-Honey-Oats-Penne-Pasta-Eggs-Chicken-Breast-Toilet-Paper-Tomatoes-Bottled-Water-Orange-Juice-Apples-and-Skyy-Vodka-totalling-58-dollars-81-cents) |
| `HEADER\|ITEMS\|PAYMENT\|DATE\|CUSTOM` | 1 | 0.1% | [Walgreens-Receipt-example-with-Nicorette-Inhaler-Nicoderm-and-2-more-items-totalling-97-dollars-40-cents](https://www.receiptfaker.com/generate/Walgreens-Receipt-example-with-Nicorette-Inhaler-Nicoderm-and-2-more-items-totalling-97-dollars-40-cents) |
| `CUSTOM\|HEADER\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Walmart-Receipt-example-with-Grilled-Beef-Sides-and-19-more-items-totalling-dollar94.30](https://www.receiptfaker.com/generate/Walmart-Receipt-example-with-Grilled-Beef-Sides-and-19-more-items-totalling-dollar94.30) |
| `HEADER\|CUSTOM\|CUSTOM\|PAYMENT\|CUSTOM\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Warehouse-Stationery-Receipt](https://www.receiptfaker.com/generate/Warehouse-Stationery-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Wasabi-Receipt](https://www.receiptfaker.com/generate/Wasabi-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM` | 1 | 0.1% | [Whataburger-Receipt](https://www.receiptfaker.com/generate/Whataburger-Receipt) |
| `CUSTOM\|HEADER\|CUSTOM\|ITEMS\|ITEMS\|CUSTOM` | 1 | 0.1% | [White-Spot-Restaurant-Receipt](https://www.receiptfaker.com/generate/White-Spot-Restaurant-Receipt) |
| `HEADER\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Wingstop-USA-Receipt](https://www.receiptfaker.com/generate/Wingstop-USA-Receipt) |
| `HEADER\|CUSTOM\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM` | 1 | 0.1% | [Winn-Dixie-Receipt](https://www.receiptfaker.com/generate/Winn-Dixie-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS\|CUSTOM\|ITEMS` | 1 | 0.1% | [Yard-House-Receipt](https://www.receiptfaker.com/generate/Yard-House-Receipt) |
| `HEADER\|CUSTOM\|CUSTOM\|CUSTOM\|CUSTOM\|ITEMS\|ITEMS\|ITEMS` | 1 | 0.1% | [Zambrero-Receipt](https://www.receiptfaker.com/generate/Zambrero-Receipt) |
| `HEADER\|ITEMS\|ITEMS\|BARCODE\|CUSTOM\|CUSTOM\|CUSTOM` | 1 | 0.1% | [Zion-Market-Receipt](https://www.receiptfaker.com/generate/Zion-Market-Receipt) |
| `HEADER\|CUSTOM\|ITEMS\|PAYMENT\|CUSTOM\|CUSTOM\|BARCODE` | 1 | 0.1% | [walmart-example-with-Zsty-Paws-FLTK-products-Debit-card-and-2-more-items-totalling-42-dollars-54-cents](https://www.receiptfaker.com/generate/walmart-example-with-Zsty-Paws-FLTK-products-Debit-card-and-2-more-items-totalling-42-dollars-54-cents) |

## `money_row_order`

**94 groups.** Order in which semantic money rows appear across the whole receipt.

*Where to see it:* The arithmetic column. ITEM>SUBTOTAL>TAX>TOTAL>TENDER>CHANGE is the classic supermarket order; NONE means the receipt shows no priced rows.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `ITEM` | 377 | 38.5% | [DSW-Receipt](https://www.receiptfaker.com/generate/DSW-Receipt) |
| `ITEM>SUBTOTAL>TAX>TOTAL>TENDER>META>AUTH` | 133 | 13.6% | [Ace-Receipt](https://www.receiptfaker.com/generate/Ace-Receipt) |
| `NONE` | 91 | 9.3% | [Belk-Receipt](https://www.receiptfaker.com/generate/Belk-Receipt) |
| `ITEM>SUBTOTAL>TAX>TOTAL>TENDER>CHANGE` | 88 | 9.0% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `ITEM>SUBTOTAL>TAX>TOTAL` | 67 | 6.8% | [GNC-Receipt](https://www.receiptfaker.com/generate/GNC-Receipt) |
| `ITEM>TOTAL` | 26 | 2.7% | [Bambu-Receipt](https://www.receiptfaker.com/generate/Bambu-Receipt) |
| `ITEM>SUBTOTAL>TOTAL` | 16 | 1.6% | [FreshCo-Receipt](https://www.receiptfaker.com/generate/FreshCo-Receipt) |
| `ITEM>TOTAL>TENDER>META>AUTH` | 15 | 1.5% | [Shell-Receipt](https://www.receiptfaker.com/generate/Shell-Receipt) |
| `ITEM>SUBTOTAL>TAX` | 11 | 1.1% | [J.Crew-Receipt](https://www.receiptfaker.com/generate/J.Crew-Receipt) |
| `ITEM>SUBTOTAL>TAX>TOTAL>TENDER` | 8 | 0.8% | [Hy-Vee-Receipt](https://www.receiptfaker.com/generate/Hy-Vee-Receipt) |
| `ITEM>SUBTOTAL>TOTAL>TENDER>META>AUTH` | 8 | 0.8% | [Uber-Receipt](https://www.receiptfaker.com/generate/Uber-Receipt) |
| `ITEM>SUBTOTAL>TOTAL>TENDER` | 7 | 0.7% | [GOAT-Receipt](https://www.receiptfaker.com/generate/GOAT-Receipt) |
| `ITEM>SUBTOTAL>TAX>TOTAL>TENDER>AUTH` | 6 | 0.6% | [Sam's-Club-Receipt](https://www.receiptfaker.com/generate/Sam's-Club-Receipt) |
| `ITEM>TOTAL>TENDER` | 5 | 0.5% | [GAGA-Receipt](https://www.receiptfaker.com/generate/GAGA-Receipt) |
| `META>ITEM>SUBTOTAL>TAX>TOTAL` | 5 | 0.5% | [All-Saints-Receipt](https://www.receiptfaker.com/generate/All-Saints-Receipt) |
| `SUBTOTAL>TAX>TOTAL>TENDER>META>AUTH>ITEM` | 4 | 0.4% | [Gas-Receipt](https://www.receiptfaker.com/generate/Gas-Receipt) |
| `ITEM>TAX>TOTAL` | 4 | 0.4% | [Vons-Receipt](https://www.receiptfaker.com/generate/Vons-Receipt) |
| `ITEM>TENDER>CHANGE` | 4 | 0.4% | [H-Mart-Receipt](https://www.receiptfaker.com/generate/H-Mart-Receipt) |
| `ITEM>TOTAL>TAX` | 3 | 0.3% | [Foot-Locker-Receipt](https://www.receiptfaker.com/generate/Foot-Locker-Receipt) |
| `ITEM>SUBTOTAL>TIP>TOTAL` | 3 | 0.3% | [Ta-Wan-Receipt](https://www.receiptfaker.com/generate/Ta-Wan-Receipt) |
| `ITEM>SUBTOTAL>TAX>TIP>TOTAL` | 3 | 0.3% | [Ceres-Receipt](https://www.receiptfaker.com/generate/Ceres-Receipt) |
| `META>ITEM>SUBTOTAL>TAX>TOTAL>TENDER>AUTH` | 3 | 0.3% | [Generic-POS-Receipt](https://www.receiptfaker.com/generate/Generic-POS-Receipt) |
| `ITEM>SUBTOTAL>TOTAL>TENDER>AUTH` | 3 | 0.3% | [PACSUN-Receipt](https://www.receiptfaker.com/generate/PACSUN-Receipt) |
| `META>ITEM>SUBTOTAL>TOTAL` | 2 | 0.2% | [Amano-Receipt](https://www.receiptfaker.com/generate/Amano-Receipt) |
| `ITEM>TOTAL>TENDER>CHANGE>TAX` | 2 | 0.2% | [Bit's-n-Bob's-Receipt](https://www.receiptfaker.com/generate/Bit's-n-Bob's-Receipt) |
| `ITEM>TAX>TENDER>CHANGE` | 2 | 0.2% | [Bojangles-Receipt](https://www.receiptfaker.com/generate/Bojangles-Receipt) |
| `ITEM>TOTAL>TENDER>TAX` | 2 | 0.2% | [Checkers-Receipt](https://www.receiptfaker.com/generate/Checkers-Receipt) |
| `ITEM>TOTAL>TAX>TENDER` | 2 | 0.2% | [Vapiano-Receipt](https://www.receiptfaker.com/generate/Vapiano-Receipt) |
| `ITEM>TENDER` | 2 | 0.2% | [Co-op-UK-Receipt](https://www.receiptfaker.com/generate/Co-op-UK-Receipt) |
| `ITEM>SUBTOTAL>TOTAL>TENDER>CHANGE` | 2 | 0.2% | [NYC-Taxi-Receipt](https://www.receiptfaker.com/generate/NYC-Taxi-Receipt) |
| `SUBTOTAL>TAX>TOTAL` | 2 | 0.2% | [DICK'S-Receipt](https://www.receiptfaker.com/generate/DICK'S-Receipt) |
| `ITEM>TENDER>TOTAL` | 2 | 0.2% | [Sainsbury's-Receipt](https://www.receiptfaker.com/generate/Sainsbury's-Receipt) |
| `ITEM>TAX>TENDER>AUTH` | 2 | 0.2% | [GIANT-Receipt](https://www.receiptfaker.com/generate/GIANT-Receipt) |
| `ITEM>TAX>TENDER>META>AUTH` | 2 | 0.2% | [Ralphs-Receipt](https://www.receiptfaker.com/generate/Ralphs-Receipt) |
| `ITEM>TOTAL>TIP` | 2 | 0.2% | [Pint-Shop-Receipt](https://www.receiptfaker.com/generate/Pint-Shop-Receipt) |
| `ITEM>TAX>TOTAL>TENDER>CHANGE` | 2 | 0.2% | [Meijer-Receipt](https://www.receiptfaker.com/generate/Meijer-Receipt) |
| `TOTAL>ITEM` | 2 | 0.2% | [Party-King-Receipt](https://www.receiptfaker.com/generate/Party-King-Receipt) |
| `META>ITEM>SUBTOTAL>TAX>TOTAL>TENDER` | 2 | 0.2% | [Portillo's-Receipt](https://www.receiptfaker.com/generate/Portillo's-Receipt) |
| `ITEM>TENDER>CHANGE>TOTAL` | 2 | 0.2% | [Tesco-Receipt](https://www.receiptfaker.com/generate/Tesco-Receipt) |
| `ITEM>SUBTOTAL>TAX>TOTAL>TENDER>META` | 2 | 0.2% | [TJ-Maxx-Receipt](https://www.receiptfaker.com/generate/TJ-Maxx-Receipt) |
| `ITEM>META` | 2 | 0.2% | [Victoria's-Secret-Receipt](https://www.receiptfaker.com/generate/Victoria's-Secret-Receipt) |
| `ITEM>META>AUTH>TENDER>TOTAL` | 1 | 0.1% | [Adidas-Receipt](https://www.receiptfaker.com/generate/Adidas-Receipt) |
| `ITEM>SUBTOTAL` | 1 | 0.1% | [Applebee's-Receipt](https://www.receiptfaker.com/generate/Applebee's-Receipt) |
| `ITEM>SUBTOTAL>TENDER>CHANGE>TOTAL` | 1 | 0.1% | [BIG-W-Receipt](https://www.receiptfaker.com/generate/BIG-W-Receipt) |
| `META>ITEM>SUBTOTAL>DISCOUNT>TOTAL>AUTH>CHANGE` | 1 | 0.1% | [Baja-Fresh-Receipt](https://www.receiptfaker.com/generate/Baja-Fresh-Receipt) |
| `ITEM>TAX>TENDER>TOTAL` | 1 | 0.1% | [Bass-Pro-Shops-Outdoor-World-Receipt](https://www.receiptfaker.com/generate/Bass-Pro-Shops-Outdoor-World-Receipt) |
| `SUBTOTAL>TAX>TOTAL>TENDER>CHANGE` | 1 | 0.1% | [Best-Buy-Sales-Receipt](https://www.receiptfaker.com/generate/Best-Buy-Sales-Receipt) |
| `ITEM>TAX>TOTAL>TENDER` | 1 | 0.1% | [Bosley's-Pet-Valu-Receipt](https://www.receiptfaker.com/generate/Bosley's-Pet-Valu-Receipt) |
| `META>ITEM>TOTAL` | 1 | 0.1% | [Bumps-Family-Restaurant-Receipt](https://www.receiptfaker.com/generate/Bumps-Family-Restaurant-Receipt) |
| `ITEM>TAX>SUBTOTAL>TOTAL>CHANGE>TENDER` | 1 | 0.1% | [Chevron-Gas-Station-Receipt](https://www.receiptfaker.com/generate/Chevron-Gas-Station-Receipt) |
| `ITEM>SUBTOTAL>AUTH>TENDER>TOTAL>CHANGE` | 1 | 0.1% | [Countdown-Supermarket-Receipt](https://www.receiptfaker.com/generate/Countdown-Supermarket-Receipt) |
| `ITEM>TOTAL>SUBTOTAL>TAX` | 1 | 0.1% | [Dick's-Sporting-Goods-Receipt](https://www.receiptfaker.com/generate/Dick's-Sporting-Goods-Receipt) |
| `ITEM>SUBTOTAL>TAX>TENDER>CHANGE` | 1 | 0.1% | [El-Pollo-Loco-Receipt](https://www.receiptfaker.com/generate/El-Pollo-Loco-Receipt) |
| `ITEM>TENDER>SUBTOTAL>TAX>TOTAL>CHANGE` | 1 | 0.1% | [Farm-Boy-Country-Market-Receipt](https://www.receiptfaker.com/generate/Farm-Boy-Country-Market-Receipt) |
| `TENDER>TOTAL>ITEM` | 1 | 0.1% | [FarmSudz-Receipt](https://www.receiptfaker.com/generate/FarmSudz-Receipt) |
| `ITEM>SUBTOTAL>TAX>TENDER>TOTAL` | 1 | 0.1% | [Four-Seasons-Siam-Paragon-Receipt](https://www.receiptfaker.com/generate/Four-Seasons-Siam-Paragon-Receipt) |
| `META>ITEM>SUBTOTAL>TAX>TOTAL>TENDER>CHANGE` | 1 | 0.1% | [Fresh-Thyme-Farmers-Market-Receipt](https://www.receiptfaker.com/generate/Fresh-Thyme-Farmers-Market-Receipt) |
| `ITEM>META>SUBTOTAL>TAX>TOTAL>TENDER>AUTH` | 1 | 0.1% | [Hardee's-Receipt](https://www.receiptfaker.com/generate/Hardee's-Receipt) |
| `ITEM>AUTH>SUBTOTAL` | 1 | 0.1% | [Hiltl-Dachterrasse-Receipt](https://www.receiptfaker.com/generate/Hiltl-Dachterrasse-Receipt) |
| `ITEM>SUBTOTAL>TIP>TAX>TOTAL` | 1 | 0.1% | [Hilton-Hotel-Receipt](https://www.receiptfaker.com/generate/Hilton-Hotel-Receipt) |
| `TOTAL>ITEM>TENDER` | 1 | 0.1% | [Hisana-Receipt](https://www.receiptfaker.com/generate/Hisana-Receipt) |
| `META>ITEM>TOTAL>TAX>TENDER>CHANGE` | 1 | 0.1% | [Joma-Bakery-Cafe-In-Store-Receipt](https://www.receiptfaker.com/generate/Joma-Bakery-Cafe-In-Store-Receipt) |
| `TENDER>META>AUTH>ITEM>SUBTOTAL>TAX>TOTAL` | 1 | 0.1% | [Kroger-Receipt-example-with-Google-Play-Card-for-200-dollars](https://www.receiptfaker.com/generate/Kroger-Receipt-example-with-Google-Play-Card-for-200-dollars) |
| `META>ITEM>TOTAL>TENDER` | 1 | 0.1% | [Krystal-LaFollette-Receipt](https://www.receiptfaker.com/generate/Krystal-LaFollette-Receipt) |
| `ITEM>SUBTOTAL>TAX>TOTAL>META>CHANGE` | 1 | 0.1% | [Kwik-Trip-Receipt](https://www.receiptfaker.com/generate/Kwik-Trip-Receipt) |
| `ITEM>TAX>TOTAL>TENDER>META>AUTH` | 1 | 0.1% | [Little-Caesars-Receipt](https://www.receiptfaker.com/generate/Little-Caesars-Receipt) |
| `ITEM>SUBTOTAL>TIP>TOTAL>TENDER>META>AUTH` | 1 | 0.1% | [Lyft-Receipt](https://www.receiptfaker.com/generate/Lyft-Receipt) |
| `ITEM>TOTAL>TAX>TIP>TENDER` | 1 | 0.1% | [Marco's-Pizza-Receipt](https://www.receiptfaker.com/generate/Marco's-Pizza-Receipt) |
| `ITEM>DISCOUNT>TENDER` | 1 | 0.1% | [Marks-and-Spencer-(MandS)-Receipt](https://www.receiptfaker.com/generate/Marks-and-Spencer-(MandS)-Receipt) |
| `ITEM>TAX>TENDER>AUTH>CHANGE` | 1 | 0.1% | [Metropolitan-Market-Receipt](https://www.receiptfaker.com/generate/Metropolitan-Market-Receipt) |
| `ITEM>TENDER>SUBTOTAL>TOTAL>META` | 1 | 0.1% | [New-World-Albany-Receipt](https://www.receiptfaker.com/generate/New-World-Albany-Receipt) |
| `TOTAL>ITEM>CHANGE` | 1 | 0.1% | [Noel-Leeming-Receipt](https://www.receiptfaker.com/generate/Noel-Leeming-Receipt) |
| `TOTAL>TAX>SUBTOTAL>TENDER>ITEM` | 1 | 0.1% | [Noodles-Kober-Receipt](https://www.receiptfaker.com/generate/Noodles-Kober-Receipt) |
| `ITEM>TENDER>CHANGE>SUBTOTAL>TOTAL` | 1 | 0.1% | [PC-Market-of-Choice-Receipt](https://www.receiptfaker.com/generate/PC-Market-of-Choice-Receipt) |
| `ITEM>TAX` | 1 | 0.1% | [Post-Office-Ltd-Self-Service-Receipt](https://www.receiptfaker.com/generate/Post-Office-Ltd-Self-Service-Receipt) |
| `ITEM>TOTAL>TAX>TENDER>META>AUTH` | 1 | 0.1% | [Publix-Receipt](https://www.receiptfaker.com/generate/Publix-Receipt) |
| `ITEM>SUBTOTAL>TAX>AUTH>CHANGE` | 1 | 0.1% | [Roche-Bros.-Receipt](https://www.receiptfaker.com/generate/Roche-Bros.-Receipt) |
| `ITEM>SUBTOTAL>TAX>TOTAL>TENDER>CHANGE>META>AUTH` | 1 | 0.1% | [Rubio's-Receipt](https://www.receiptfaker.com/generate/Rubio's-Receipt) |
| `ITEM>TOTAL>META` | 1 | 0.1% | [Saint-Laurent-Paris-Receipt](https://www.receiptfaker.com/generate/Saint-Laurent-Paris-Receipt) |
| `ITEM>TIP>TOTAL` | 1 | 0.1% | [Salt-and-Straw-Receipt](https://www.receiptfaker.com/generate/Salt-and-Straw-Receipt) |
| `ITEM>TOTAL>TENDER>CHANGE` | 1 | 0.1% | [Square-POS-Receipt](https://www.receiptfaker.com/generate/Square-POS-Receipt) |
| `ITEM>DISCOUNT>SUBTOTAL>TAX>TOTAL>TENDER>AUTH` | 1 | 0.1% | [Sunglass-Hut-Receipt](https://www.receiptfaker.com/generate/Sunglass-Hut-Receipt) |
| `SUBTOTAL>TOTAL>ITEM>CHANGE` | 1 | 0.1% | [Super-Food-Aruba-Receipt](https://www.receiptfaker.com/generate/Super-Food-Aruba-Receipt) |
| `ITEM>META>SUBTOTAL>TAX>TOTAL>TENDER>CHANGE` | 1 | 0.1% | [Taco-Cabana-Denton-Receipt](https://www.receiptfaker.com/generate/Taco-Cabana-Denton-Receipt) |
| `META>ITEM>DISCOUNT>AUTH>SUBTOTAL>TAX>TOTAL` | 1 | 0.1% | [Taxi-Ride-Receipt](https://www.receiptfaker.com/generate/Taxi-Ride-Receipt) |
| `META>ITEM>SUBTOTAL>TAX>TOTAL>TIP` | 1 | 0.1% | [The-Armory-Receipt](https://www.receiptfaker.com/generate/The-Armory-Receipt) |
| `ITEM>SUBTOTAL>TENDER` | 1 | 0.1% | [The-Crosby-Receipt](https://www.receiptfaker.com/generate/The-Crosby-Receipt) |
| `ITEM>SUBTOTAL>TAX>TOTAL>TIP` | 1 | 0.1% | [Uncle-Paul's-Pizza-Receipt](https://www.receiptfaker.com/generate/Uncle-Paul's-Pizza-Receipt) |
| `ITEM>SUBTOTAL>TAX>TOTAL>CHANGE` | 1 | 0.1% | [Valero-Gas-Station-Receipt](https://www.receiptfaker.com/generate/Valero-Gas-Station-Receipt) |
| `TENDER>ITEM` | 1 | 0.1% | [Visionworks-Receipt](https://www.receiptfaker.com/generate/Visionworks-Receipt) |
| `ITEM>CHANGE` | 1 | 0.1% | [Waitrose-and-Partners-Receipt](https://www.receiptfaker.com/generate/Waitrose-and-Partners-Receipt) |
| `ITEM>AUTH>TENDER>TOTAL` | 1 | 0.1% | [Warehouse-Stationery-Receipt](https://www.receiptfaker.com/generate/Warehouse-Stationery-Receipt) |
| `ITEM>TENDER>SUBTOTAL>TAX` | 1 | 0.1% | [Zaxby's-US-Receipt](https://www.receiptfaker.com/generate/Zaxby's-US-Receipt) |
| `ITEM>SUBTOTAL>TENDER>CHANGE` | 1 | 0.1% | [Zion-Market-Receipt](https://www.receiptfaker.com/generate/Zion-Market-Receipt) |

## `section_count`

**15 groups.** Number of stacked blocks making up the receipt.

*Where to see it:* A proxy for overall complexity and length -- count the visually distinct bands from logo to footer.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `6` | 198 | 20.2% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `5` | 192 | 19.6% | [GNC-Receipt](https://www.receiptfaker.com/generate/GNC-Receipt) |
| `7` | 179 | 18.3% | [Ace-Receipt](https://www.receiptfaker.com/generate/Ace-Receipt) |
| `4` | 120 | 12.3% | [Cub-Receipt](https://www.receiptfaker.com/generate/Cub-Receipt) |
| `8` | 113 | 11.5% | [Vet-Receipt](https://www.receiptfaker.com/generate/Vet-Receipt) |
| `9` | 65 | 6.6% | [Gas-Receipt](https://www.receiptfaker.com/generate/Gas-Receipt) |
| `3` | 57 | 5.8% | [Belk-Receipt](https://www.receiptfaker.com/generate/Belk-Receipt) |
| `10` | 23 | 2.3% | [SMYK-Receipt](https://www.receiptfaker.com/generate/SMYK-Receipt) |
| `11` | 11 | 1.1% | [ORLEN-Receipt](https://www.receiptfaker.com/generate/ORLEN-Receipt) |
| `2` | 8 | 0.8% | [Kmart-Receipt](https://www.receiptfaker.com/generate/Kmart-Receipt) |
| `12` | 7 | 0.7% | [USPS-Receipt](https://www.receiptfaker.com/generate/USPS-Receipt) |
| `13` | 2 | 0.2% | [Adidas-Receipt](https://www.receiptfaker.com/generate/Adidas-Receipt) |
| `15` | 2 | 0.2% | [Biedronka-Receipt](https://www.receiptfaker.com/generate/Biedronka-Receipt) |
| `1` | 1 | 0.1% | [THE-PORT-AUTHORITY-Receipt](https://www.receiptfaker.com/generate/THE-PORT-AUTHORITY-Receipt) |
| `16` | 1 | 0.1% | [Veerman-Juwelen-Receipt](https://www.receiptfaker.com/generate/Veerman-Juwelen-Receipt) |

## `divider_style`

**7 groups.** Dominant separator character drawn between stacked blocks.

*Where to see it:* The horizontal rules splitting header from items from totals. EMPTY is a blank line rather than a drawn rule; NONE means blocks abut directly.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `DASHES` | 396 | 40.4% | [Ace-Receipt](https://www.receiptfaker.com/generate/Ace-Receipt) |
| `NONE` | 273 | 27.9% | [Cub-Receipt](https://www.receiptfaker.com/generate/Cub-Receipt) |
| `EMPTY` | 215 | 22.0% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `EQUALS` | 34 | 3.5% | [Blend-Receipt](https://www.receiptfaker.com/generate/Blend-Receipt) |
| `STARS` | 34 | 3.5% | [Vet-Receipt](https://www.receiptfaker.com/generate/Vet-Receipt) |
| `COLONS` | 21 | 2.1% | [Dental-Receipt](https://www.receiptfaker.com/generate/Dental-Receipt) |
| `DOTS` | 6 | 0.6% | [Gas-Receipt](https://www.receiptfaker.com/generate/Gas-Receipt) |

## `total_divider_style`

**7 groups.** Separator drawn immediately above the grand-total row.

*Where to see it:* The rule between the last line item (or tax row) and the TOTAL line.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `NONE` | 518 | 52.9% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `DASHES` | 316 | 32.3% | [Ace-Receipt](https://www.receiptfaker.com/generate/Ace-Receipt) |
| `EMPTY` | 94 | 9.6% | [GAP-Receipt](https://www.receiptfaker.com/generate/GAP-Receipt) |
| `EQUALS` | 25 | 2.6% | [Bambu-Receipt](https://www.receiptfaker.com/generate/Bambu-Receipt) |
| `STARS` | 13 | 1.3% | [Labor-Receipt](https://www.receiptfaker.com/generate/Labor-Receipt) |
| `DOTS` | 9 | 0.9% | [Nanny-Receipt](https://www.receiptfaker.com/generate/Nanny-Receipt) |
| `COLONS` | 4 | 0.4% | [Vet-Receipt](https://www.receiptfaker.com/generate/Vet-Receipt) |

## `total_emphasis`

**6 groups.** Font-size increase applied to the grand-total row relative to body text.

*Where to see it:* The TOTAL line. PERCENT_50 renders it half again as large; NONE keeps it the same size as the line items above it.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `NONE` | 888 | 90.7% | [Ace-Receipt](https://www.receiptfaker.com/generate/Ace-Receipt) |
| `PERCENT_20` | 29 | 3.0% | [Vet-Receipt](https://www.receiptfaker.com/generate/Vet-Receipt) |
| `PERCENT_50` | 27 | 2.8% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `PERCENT_10` | 24 | 2.5% | [Dior-Receipt](https://www.receiptfaker.com/generate/Dior-Receipt) |
| `PERCENT_75` | 7 | 0.7% | [Bakery-Receipt](https://www.receiptfaker.com/generate/Bakery-Receipt) |
| `PERCENT_100` | 4 | 0.4% | [Hotel-Receipt](https://www.receiptfaker.com/generate/Hotel-Receipt) |

## `background_type`

**6 groups.** Paper texture composited behind the rendered text.

*Where to see it:* The substrate itself -- crumple pattern, shadowing and creases. Purely a photorealism treatment; it does not move any content.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `CRUMPLED_1` | 882 | 90.1% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `UNSET` | 72 | 7.4% | [Hotel-Receipt](https://www.receiptfaker.com/generate/Hotel-Receipt) |
| `CRUMPLED_4` | 11 | 1.1% | [LIDL-Receipt](https://www.receiptfaker.com/generate/LIDL-Receipt) |
| `CRUMPLED_5` | 6 | 0.6% | [Clothes-Quarters-Receipt](https://www.receiptfaker.com/generate/Clothes-Quarters-Receipt) |
| `CRUMPLED_2` | 5 | 0.5% | [Ace-Receipt](https://www.receiptfaker.com/generate/Ace-Receipt) |
| `CRUMPLED_3` | 3 | 0.3% | [USPS-Receipt](https://www.receiptfaker.com/generate/USPS-Receipt) |

## `font_type`

**4 groups.** Typeface family the entire receipt body is rendered in.

*Where to see it:* Everywhere. Easiest to judge on digits and capitals in the total row -- MERCHANT_COPY is the narrow dot-matrix thermal face, FAKE_RECEIPT and RECEIPTIONAL_RECEIPT are wider and rounder.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `MERCHANT_COPY` | 901 | 92.0% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `UNSET` | 52 | 5.3% | [Petco-Receipt](https://www.receiptfaker.com/generate/Petco-Receipt) |
| `FAKE_RECEIPT` | 16 | 1.6% | [Lush-Receipt](https://www.receiptfaker.com/generate/Lush-Receipt) |
| `RECEIPTIONAL_RECEIPT` | 10 | 1.0% | [JOZY-Receipt](https://www.receiptfaker.com/generate/JOZY-Receipt) |

## `logo_placement`

**4 groups.** Vertical position of the brand logo image, or its absence.

*Where to see it:* The graphic at the very top of most receipts. BOTTOM puts it below the totals, near the thank-you message.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `TOP` | 773 | 79.0% | [Ace-Receipt](https://www.receiptfaker.com/generate/Ace-Receipt) |
| `NONE` | 183 | 18.7% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `MIDDLE` | 21 | 2.1% | [Masters-Receipt](https://www.receiptfaker.com/generate/Masters-Receipt) |
| `BOTTOM` | 2 | 0.2% | [Razz-Coffee-Receipt](https://www.receiptfaker.com/generate/Razz-Coffee-Receipt) |

## `barcode_placement`

**4 groups.** Vertical position of the barcode block, or its absence.

*Where to see it:* The scannable stripe, usually near the foot of the receipt below the totals and above or below the thank-you message.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `NONE` | 639 | 65.3% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `MIDDLE` | 227 | 23.2% | [DSW-Receipt](https://www.receiptfaker.com/generate/DSW-Receipt) |
| `BOTTOM` | 112 | 11.4% | [Ace-Receipt](https://www.receiptfaker.com/generate/Ace-Receipt) |
| `TOP` | 1 | 0.1% | [Cracker-Barrel-Receipt](https://www.receiptfaker.com/generate/Cracker-Barrel-Receipt) |

## `number_format`

**4 groups.** Horizontal alignment of the amount column.

*Where to see it:* The price column on the right. LEFT ragged-aligns the amounts; RIGHT and RIGHT_SPACE align them flush so decimal points line up.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `LEFT` | 896 | 91.5% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `UNSET` | 75 | 7.7% | [Hotel-Receipt](https://www.receiptfaker.com/generate/Hotel-Receipt) |
| `RIGHT_SPACE` | 4 | 0.4% | [Splend'Or-Receipt](https://www.receiptfaker.com/generate/Splend'Or-Receipt) |
| `RIGHT` | 4 | 0.4% | [Selfridges-Receipt](https://www.receiptfaker.com/generate/Selfridges-Receipt) |

## `header_alignment`

**4 groups.** Text alignment inside the header block.

*Where to see it:* The merchant name and address lines. CENTER is the thermal-printer norm; LEFT reads more like an invoice.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `CENTER` | 896 | 91.5% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `LEFT` | 74 | 7.6% | [DSW-Receipt](https://www.receiptfaker.com/generate/DSW-Receipt) |
| `RIGHT` | 6 | 0.6% | [StockX-Receipt](https://www.receiptfaker.com/generate/StockX-Receipt) |
| `UNSET` | 3 | 0.3% | [Van's-Burgers-Receipt](https://www.receiptfaker.com/generate/Van's-Burgers-Receipt) |

## `merchant_block_position`

**3 groups.** Vertical position of the block holding the merchant name and address.

*Where to see it:* The store name, street, city and phone number. Nearly always the first block under the logo; MIDDLE means it appears after some other block.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `TOP` | 953 | 97.3% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `MIDDLE` | 23 | 2.3% | [PACSUN-Receipt](https://www.receiptfaker.com/generate/PACSUN-Receipt) |
| `NONE` | 3 | 0.3% | [Van's-Burgers-Receipt](https://www.receiptfaker.com/generate/Van's-Burgers-Receipt) |

## `quantity_column`

**3 groups.** Whether line items render a leading quantity column.

*Where to see it:* The left edge of the item table -- a '2' before the product name. NO_ITEMS covers receipts with no itemised purchase table at all.

| Group | Count | Share | Example template |
| --- | ---: | ---: | --- |
| `PRESENT` | 432 | 44.1% | [BP-Receipt](https://www.receiptfaker.com/generate/BP-Receipt) |
| `ABSENT` | 388 | 39.6% | [Cub-Receipt](https://www.receiptfaker.com/generate/Cub-Receipt) |
| `NO_ITEMS` | 159 | 16.2% | [Gas-Receipt](https://www.receiptfaker.com/generate/Gas-Receipt) |
