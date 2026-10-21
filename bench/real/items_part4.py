ITEMS = [
    dict(id="R-S25", label=1, date="2026-08-17", channel="sms", source="Outlook Money (PIB Fact Check), 17 Aug 2026", form="excerpts",
         url="https://www.outlookmoney.com/amp/story/tax/income-tax-notice-seeking-rs-6000-is-fake-heres-what-taxpayers-should-do",
         text="Received an Income Tax Department (ITD) notice asking you to deposit Rs 6,000? "
              "In some cases, the message may direct the taxpayer to a link for making the supposed payment. "
              "They may carry logos, use formal language, and ask the recipient to act quickly.",
         gold=dict(agencies=["income_tax"], instruments=["tax_notice"], demands=["transfer_funds"], payee="caller_supplied")),
    dict(id="R-S26", label=1, date="2026-03-11", channel="email", source="Outlook Money, 11 Mar 2026", form="excerpts",
         url="https://www.outlookmoney.com/tax/urgent-alert-income-tax-department-flags-fake-ay-202526-demand-notices",
         text="An email is circulating online claiming to be issued by the Income Tax Department for Assessment Year 2025-26. "
              "The email further asks recipients to pay a tax demand and directs them to click a link to view an 'Assessment Order.'",
         gold=dict(agencies=["income_tax"], instruments=["tax_notice"], demands=["transfer_funds"], payee="caller_supplied")),

    dict(id="R-L11", label=0, date="2026-02-19", channel="physical", source="Outlook Business, 19 Feb 2026", form="excerpts",
         url="https://www.outlookbusiness.com/corporate/ed-issues-fresh-summons-to-anil-ambani-for-february-26",
         text="The Enforcement Directorate has issued fresh summons to Reliance Group chairman Anil Ambani "
              "to appear for questioning on February 26 after he skipped deposition this week, "
              "record their separate statements under the Prevention of Money Laundering Act (PMLA).",
         gold=dict(agencies=["ed"], instruments=["summons_ed"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L12", label=0, date="2025-06-20", channel="physical", source="Onmanorama, 24 Jun 2025", form="excerpts",
         url="https://www.onmanorama.com/news/kerala/2025/06/24/manjummel-boys-producers-bail.amp.html",
         text="they had received a notice under Section 35(3) of the Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023. "
              "As per the notice, the petitioners were required to appear at the Police Station on June 20.",
         gold=dict(agencies=["police"], instruments=["notice_s35"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L13", label=0, date="2024-03-17", channel="physical", source="Business Standard, 17 Mar 2024", form="excerpts",
         url="https://www.business-standard.com/politics/ed-issues-fresh-summons-to-delhi-cm-kejriwal-asked-to-appear-on-march-21-124031700086_1.html",
         text="The Enforcement Directorate has issued fresh summons, "
              "to appear for questioning on March 21 in the excise policy linked money laundering case, "
              "so that Kejriwal's statement can be recorded under the Prevention of Money Laundering Act. "
              "has been asked to depose at the central agency's office in central Delhi.",
         gold=dict(agencies=["ed"], instruments=["summons_ed"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L14", label=0, date="2025-04-18", channel="physical", source="The Week (PTI), 18 Apr 2025", form="excerpts",
         url="https://www.theweek.in/wire-updates/national/2025/04/18/mes14-kl-actor-police-notice.html",
         text="the notice was delivered to the actor's family at his residence in Thrissur, "
              "directing him to appear for questioning in connection with an incident. "
              "Chacko has been asked to appear before the Ernakulam North Police Sub-Inspector at 10 am on Saturday.",
         gold=dict(agencies=["police"], instruments=["notice_s35"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L15", label=0, date="2025-12-24", channel="sms", source="Business Standard, 24 Dec 2025", form="excerpts",
         url="https://www.business-standard.com/finance/news/i-t-dept-flags-discrepancies-in-returns-extends-deadline-to-december-31-125122200741_1.html",
         text="text messages from the income tax (I-T) department asking them to file revised returns by December 31, "
              "claiming discrepancies were identified in their refund claims. "
              "aims to prompt voluntary compliance by flagging potential errors identified through risk analytics.",
         gold=dict(agencies=["income_tax"], instruments=["tax_notice"], demands=["pay_via_portal"], payee="official_portal")),
]
