"""TEST phrase bank: written after the claim extractor was frozen, with different
wording (including Indian-English and Hinglish turns of phrase) to measure
generalisation of the whole pipeline to unseen surface forms."""

from bench.phrases_dev import g

P = {
    "intro_courier": [
        ("Hello, I am calling from the logistics company, your shipment to Cambodia has been held by customs at Mumbai airport.", g(["courier", "customs"])),
        ("Sir, ek parcel aapke naam pe book hua hai, customs ne pakad liya hai.", g(["courier", "customs"])),
        ("Your consignment booked through our courier has been intercepted, it is lying with the authorities.", g(["courier"])),
    ],
    "drugs": [
        ("Inside it we found 140 grams of drugs, a laptop and several SIM cards.", g()),
        ("There are banned narcotic substances in the package and a few fake ID cards.", g()),
        ("Contraband material was recovered from your parcel.", g()),
    ],
    "transfer_police": [
        ("Let me connect you to the Delhi Police crime branch, they will take your statement.", g(["police"])),
        ("I am forwarding the call to the cyber police; the officer will join on video.", g(["police"])),
        ("A CBI official is coming on the line now, please accept the video call.", g(["cbi"])),
    ],
    "aadhaar_laundering": [
        ("Your Aadhaar details were misused to open accounts that received crores of black money.", g()),
        ("An Enforcement Directorate case for money laundering has your name and Aadhaar on it.", g(["ed"])),
        ("Your PAN and Aadhaar are linked with an illegal money transfer racket.", g()),
    ],
    "officer_self": [
        ("My name is Sub-Inspector Patil, cyber crime police station.", g(["police"])),
        ("Senior officer Mishra speaking from the Central Bureau of Investigation.", g(["cbi"])),
        ("This is Deputy Director Khan from the ED office.", g(["ed"])),
        ("I am speaking from the NCB, narcotics wing.", g(["ncb"])),
    ],
    "arrest_by_call": [
        ("Till the inquiry is over you are digitally arrested, this call itself is your custody.", g(i=["arrest"])),
        ("Aapko abhi isi video call par arrest kiya ja raha hai.", g(i=["arrest"])),
        ("A warrant of arrest is out against you and you are in our custody on this call.", g(i=["arrest", "arrest_warrant"])),
    ],
    "stay_on_camera": [
        ("Don't move away from the screen, we need to see you every minute.", g(d=["stay_on_camera"])),
        ("Keep the video running, even at night; you are under surveillance.", g(d=["stay_on_camera"])),
        ("Camera band mat karna, hum aapko monitor kar rahe hain.", g(d=["stay_on_camera"])),
    ],
    "secrecy": [
        ("Do not share this with your wife or children, it will spoil the investigation.", g(d=["secrecy"])),
        ("Kisi ko mat batana, warna aapke parivaar ko bhi uthaya jayega.", g(d=["secrecy"])),
        ("This matter is top secret; speaking to anyone is a criminal offence.", g(d=["secrecy"])),
    ],
    "transfer_verification": [
        ("Shift your fixed deposits into the government verification account; after clearance the money will come back.",
         g(d=["transfer_funds", "verification_deposit"], payee="caller_supplied")),
        ("Please put the entire balance in this account for checking the source of funds; it is refundable within 24 hours.",
         g(d=["transfer_funds", "verification_deposit"], payee="caller_supplied")),
        ("Paisa is account me daal do, verification ke baad wapas mil jayega.",
         g(d=["transfer_funds", "verification_deposit"], payee="caller_supplied")),
    ],
    "rbi_safe": [
        ("Your savings will be parked in a secure RBI escrow till you are cleared.", g(["rbi"], d=["safe_account"], payee="rbi")),
        ("Move the funds to the Reserve Bank supervision account for audit.", g(["rbi"], d=["safe_account", "verification_deposit"], payee="rbi")),
    ],
    "bail_online": [
        ("For online bail send the security deposit through UPI right now.", g(d=["bail_payment_online"], payee="caller_supplied")),
        ("Bail ke liye 1,80,000 rupaye is UPI par bhejiye.", g(d=["bail_payment_online"], payee="caller_supplied")),
    ],
    "trai_disconnect": [
        ("Calling from TRAI, all numbers on your Aadhaar will be suspended in two hours.", g(["trai"], i=["disconnection_notice"])),
        ("Telecom regulator here: your SIM is being deactivated because of complaints.", g(["trai"], i=["disconnection_notice"])),
    ],
    "tax_demand_scam": [
        ("Income-tax officer speaking: your outstanding tax must be cleared today by bank transfer to the account I send.",
         g(["income_tax"], i=["tax_notice"], d=["transfer_funds"], payee="caller_supplied")),
        ("Tax department penalty is due, remit it now to the given account or a warrant will be issued.",
         g(["income_tax"], i=["tax_notice"], d=["transfer_funds"], payee="caller_supplied")),
    ],
    "appear_in_person": [
        ("Please come to the office personally on the given date along with the original papers.", g(d=["appear_in_person"])),
        ("You have to report physically to the investigating officer at the police station.", g(["police"], d=["appear_in_person"])),
        ("You must be present before the court on the fixed date.", g(["court"], d=["appear_in_person"])),
    ],
    "produce_docs": [
        ("Kindly submit copies of the listed records by email; you need not come in person.", g(i=["order_produce_docs"], d=["produce_documents"])),
        ("Provide the documents mentioned below to the investigating officer by post or email.", g(i=["order_produce_docs"], d=["produce_documents"])),
    ],
    "vc_hearing": [
        ("You may depose through the court's video link from the designated centre.", g(["court"], i=["hearing_vc"])),
        ("The examination will happen over video conferencing as allowed by the court.", g(["court"], i=["hearing_vc"])),
    ],
    "tax_portal": [
        ("Kindly file your reply on the income tax e-filing website.", g(["income_tax"])),
        ("If any amount is payable, generate a challan on the official portal and pay there.", g(["income_tax"], d=["pay_via_portal"], payee="official_portal")),
    ],
    "bank_alert": [
        ("Hello, this is the security desk of your bank; a large card payment was attempted just now.", g(["bank"])),
        ("We have put your card on hold. Please call the customer care number on your card or visit the branch.", g(["bank"])),
        ("Please don't share any OTP with anyone; if money was lost you can complain to the police.", g(["police"])),
    ],
    "news_chat": [
        ("Arre, did you read that the CBI raided the builder's office?", g(["cbi"])),
        ("Uncle was telling the police caught the chain snatcher near the market.", g(["police"])),
        ("Our land matter is listed in court next week, I'll update you.", g(["court"])),
    ],
    "s35_whatsapp": [
        ("Notice under Section 35 BNSS forwarded on WhatsApp; you must join the video interrogation now.", g(["police"], i=["notice_s35"])),
        ("41A CrPC notice sent to your WhatsApp, come on video call immediately for inquiry.", g(["police"], i=["notice_s35"])),
    ],
    "s35_lawful": [
        ("A Section 35 BNSS notice was handed over at your house; please report to the police station.",
         g(["police"], i=["notice_s35"], d=["appear_in_person"])),
    ],
    "summons_attached": [
        ("Attaching the summons from the court for your reference.", g(["court"], i=["summons_court"])),
        ("Court has issued an e-summons in your name, copy enclosed.", g(["court"], i=["summons_court"])),
    ],
}
