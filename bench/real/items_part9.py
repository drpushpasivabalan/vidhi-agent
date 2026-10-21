ITEMS = [
    dict(id="R-L27", label=0, date="2024-02-03", channel="physical", source="Deccan Herald, 3 Feb 2024", form="excerpts",
         url="https://www.deccanherald.com/amp/story/india%2Fdelhi%2Faap-mla-poaching-claims-delhi-police-serve-notice-to-kejriwal-after-2-days-of-high-drama-2878180",
         text="Delhi Police on Saturday served a notice on Chief Minister Arvind Kejriwal asking him to respond within three days, "
              "asking him to provide the names of AAP MLAs who were claimed to have been approached by the BJP. "
              "they will have to hand it over in person to the Chief Minister.",
         gold=dict(agencies=["police"], instruments=["order_produce_docs"], demands=["produce_documents"], payee="none")),
    dict(id="R-L28", label=0, date="2025-06-16", channel="physical", source="The Tribune, 16 Jun 2025", form="excerpts",
         url="https://www.tribuneindia.com/news/india/ed-issues-fresh-summons-to-robert-vadra-in-sanjay-bhandari-linked-pmla-case",
         text="The Enforcement Directorate (ED) has issued a fresh summons to Robert Vadra "
              "for questioning in a money laundering case linked to UK-based arms consultant Sanjay Bhandari. "
              "He has been asked to depose before the federal probe agency here on June 17.",
         gold=dict(agencies=["ed"], instruments=["summons_ed"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L29", label=0, date="2024-10-03", channel="email", source="NSE disclosure by Fedbank Financial Services, 6 Oct 2024", form="excerpts",
         url="https://nsearchives.nseindia.com/corporate/FEDFINA_06102024205802_GST_Intimation_signed_final.pdf",
         text="the Company has received a GST summons issued under Section 70 of the Central Goods and Service Tax Act, 2017 "
              "seeking documents/ details regarding certain type of transactions. "
              "I do hereby summon you to appear before me in person on 2024-10-16.",
         gold=dict(agencies=["tax_other"], instruments=["summons_agency"], demands=["appear_in_person", "produce_documents"], payee="none")),
]
