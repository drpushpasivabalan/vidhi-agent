ITEMS = [
    dict(id="R-S39", label=1, date="2024-12-09", channel="whatsapp", source="News24 (PIB Fact Check), 9 Dec 2024", form="excerpts",
         url="https://news24online.com/trending/beware-of-digital-arrests-pib-uncovers-fake-cybercrime-letters-used-to-trap-victims/403478/amp",
         text="A fake letter allegedly issued by the Indian Cyber Crime Coordination Centre (I4C) has been received by people "
              "with several allegations leveled against them, and a reply is sought to avoid arrest. "
              "Reports indicate that the gang contacts people via WhatsApp, posing as representatives of a courier company. "
              "They then transfer the call to someone pretending to be a police officer.",
         gold=dict(agencies=["police", "courier"], instruments=["legal_notice", "arrest"], demands=[], payee="none")),
    dict(id="R-S40", label=1, date="2026-03-28", channel="whatsapp", source="Free Press Journal, 28 Mar 2026", form="excerpts",
         url="https://www.freepressjournal.in/amp/mumbai/cbi-probes-2-crore-digital-arrest-scam-linked-to-mumbai-punjab-retiree-duped-by-fake-police",
         text="The scammers approached the victim claiming to be police officials, "
              "stated that a SIM card issued in his name was being used for illegal activities in Mumbai, "
              "stating that the money would be verified by the RBI. sent a bogus RBI letter to the victim on WhatsApp. "
              "induced the victim to send money to different bank accounts.",
         gold=dict(agencies=["police", "rbi"], instruments=[], demands=["transfer_funds", "verification_deposit"], payee="rbi")),

    dict(id="R-L30", label=0, date="2023-04-14", channel="physical", source="Business Standard, 14 Apr 2023", form="excerpts",
         url="https://www.business-standard.com/india-news/cbi-summons-delhi-cm-kejriwal-in-excise-policy-scam-case-on-sunday-123041400717_1.html",
         text="The CBI on Friday summoned Delhi Chief Minister Arvind Kejriwal on April 16. "
              "Kejriwal has been called to appear at the agency headquarters at 11 AM on Sunday "
              "to answer queries of the investigating team as a witness in the case.",
         gold=dict(agencies=["cbi"], instruments=["notice_witness"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L31", label=0, date="2024-10-04", channel="physical", source="Kashmir Life, 5 Oct 2024", form="excerpts",
         url="https://kashmirlife.net/court-summons-rahul-gandhi-on-oct-23-in-defamation-case-368435/",
         text="The court issued the summons to Gandhi on Friday, asking him to appear before it on October 23. "
              "he is required to appear in person before the court on October 23. "
              "his attendance is necessary to answer a charge punishable under section 500 (defamation).",
         gold=dict(agencies=["court"], instruments=["summons_court"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L32", label=0, date="2024-12-03", channel="physical", source="Swarajya, 3 Dec 2024", form="excerpts",
         url="https://swarajyamag.com/amp/story/news-brief/savarkar-defamation-case-pune-court-summons-rahul-gandhi-in-january-after-congress-leader-seeks-exemption-for-parliament-session",
         text="A special court in Pune has granted Congress President Rahul Gandhi an extension to appear in a defamation case. "
              "The court directed Gandhi to appear on 10 January 2025.",
         gold=dict(agencies=["court"], instruments=["summons_court"], demands=["appear_in_person"], payee="none")),
]
