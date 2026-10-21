"""DEV phrase bank: (text, gold) pairs. The claim extractor's lexicon was built only
from this file. The TEST bank (phrases_test.py) was written afterwards with
different wording and the extractor was not changed after that."""

A, I, D = "agencies", "instruments", "demands"


def g(a=(), i=(), d=(), payee=None):
    out = {A: list(a), I: list(i), D: list(d)}
    if payee:
        out["payee"] = payee
    return out


P = {
    "intro_courier": [
        ("This is calling from the courier company. A parcel booked in your name to Taiwan has been seized by customs.", g(["courier", "customs"])),
        ("Sir, your parcel sent through our courier service was stopped by customs officials.", g(["courier", "customs"])),
        ("Madam, we are from the courier office, a package in your name is held at the airport.", g(["courier"])),
    ],
    "drugs": [
        ("It contains 200 grams of MDMA drugs, five passports and three credit cards.", g()),
        ("Narcotics were found inside the parcel along with fake passports.", g()),
        ("The package has illegal drugs, so a case is registered against you.", g()),
    ],
    "transfer_police": [
        ("I am transferring your call to the Mumbai Police cyber crime branch.", g(["police"])),
        ("Your call is being connected to the police officer handling the case.", g(["police"])),
        ("Please hold, the CBI officer will now speak to you on video call.", g(["cbi"])),
    ],
    "aadhaar_laundering": [
        ("Your Aadhaar card has been used to open a bank account used in money laundering.", g()),
        ("A money laundering case has been registered against your Aadhaar number by the Enforcement Directorate.", g(["ed"])),
        ("Your bank account is linked to a hawala and money laundering racket.", g()),
    ],
    "officer_self": [
        ("I am Inspector Sharma from the Crime Branch.", g(["police"])),
        ("This is Deputy Superintendent Rao, CBI.", g(["cbi"])),
        ("I am an Assistant Director, Enforcement Directorate.", g(["ed"])),
        ("I am Officer Verma from the Narcotics Control Bureau.", g(["ncb"])),
    ],
    "arrest_by_call": [
        ("You are under digital arrest from this moment.", g(i=["arrest"])),
        ("Consider yourself arrested, the arrest will be done on this video call.", g(i=["arrest"])),
        ("An arrest warrant has been issued and you are now under arrest on this call.", g(i=["arrest", "arrest_warrant"])),
    ],
    "stay_on_camera": [
        ("Keep your camera on at all times and do not leave the room.", g(d=["stay_on_camera"])),
        ("You must stay on video call until the investigation is complete.", g(d=["stay_on_camera"])),
        ("Do not switch off the camera, we are monitoring you.", g(d=["stay_on_camera"])),
    ],
    "secrecy": [
        ("Do not tell anyone about this, not even your family members.", g(d=["secrecy"])),
        ("This is a confidential national security matter, you cannot discuss it with anyone.", g(d=["secrecy"])),
        ("If you inform anybody your family will also be arrested.", g(d=["secrecy"])),
    ],
    "transfer_verification": [
        ("Transfer all the money in your account to the verification account we give you, it will be returned after verification.",
         g(d=["transfer_funds", "verification_deposit"], payee="caller_supplied")),
        ("You have to move your funds to this account for RBI verification, it is fully refundable.",
         g(["rbi"], d=["transfer_funds", "verification_deposit"], payee="caller_supplied")),
        ("Send the amount by RTGS to the account number I am sharing for fund verification.",
         g(d=["transfer_funds", "verification_deposit"], payee="caller_supplied")),
    ],
    "rbi_safe": [
        ("The money will be kept in an RBI safe account until the case is cleared.", g(["rbi"], d=["safe_account"], payee="rbi")),
        ("Deposit the funds in the Reserve Bank account for legal verification.",
         g(["rbi"], d=["safe_account", "verification_deposit"], payee="rbi")),
    ],
    "bail_online": [
        ("To get bail you must pay the bail amount online through UPI now.", g(d=["bail_payment_online"], payee="caller_supplied")),
        ("Pay the bail security of Rs 2,50,000 to this UPI ID to avoid jail.", g(d=["bail_payment_online"], payee="caller_supplied")),
    ],
    "trai_disconnect": [
        ("This is from TRAI. Your mobile number will be disconnected within two hours due to illegal activities.",
         g(["trai"], i=["disconnection_notice"])),
        ("Telecom Regulatory Authority notice: all your SIM cards will be blocked today.", g(["trai"], i=["disconnection_notice"])),
    ],
    "tax_demand_scam": [
        ("You have pending income tax dues, pay immediately to this account or face arrest.",
         g(["income_tax"], i=["tax_notice"], d=["transfer_funds"], payee="caller_supplied")),
        ("Income tax department: penalty must be transferred today to the account given below.",
         g(["income_tax"], i=["tax_notice"], d=["transfer_funds"], payee="caller_supplied")),
    ],
    "appear_in_person": [
        ("You are required to appear in person at the office on the date mentioned with the documents.", g(d=["appear_in_person"])),
        ("Kindly appear in person before the investigating officer at the police station.", g(["police"], d=["appear_in_person"])),
        ("You are directed to attend the court in person on the next date of hearing.", g(["court"], d=["appear_in_person"])),
    ],
    "produce_docs": [
        ("You are required to produce the bank statements and documents listed below by email.",
         g(i=["order_produce_docs"], d=["produce_documents"])),
        ("Kindly produce the following documents; personal attendance is not required.", g(i=["order_produce_docs"], d=["produce_documents"])),
    ],
    "vc_hearing": [
        ("The hearing will be conducted through video conference; the link is given in the summons.", g(["court"], i=["hearing_vc"])),
        ("Your evidence will be recorded by video conferencing from the court's designated centre.", g(["court"], i=["hearing_vc"])),
    ],
    "tax_portal": [
        ("Please respond on the e-filing portal within thirty days.", g(["income_tax"])),
        ("Any demand may be paid through the challan on the official e-filing portal.", g(["income_tax"], d=["pay_via_portal"], payee="official_portal")),
    ],
    "bank_alert": [
        ("This is your bank's fraud monitoring team. We noticed an unusual transaction on your card.", g(["bank"])),
        ("We have blocked a suspicious payment. Please call the number printed on the back of your card to confirm.", g(["bank"])),
        ("We will never ask for your OTP or PIN. You may also lodge a police complaint if needed.", g(["police"])),
    ],
    "news_chat": [
        ("Did you see the news about the CBI arrest of that minister?", g(["cbi"])),
        ("My cousin is a lawyer, he says the police arrested someone in the bank fraud case.", g(["police"])),
        ("The court hearing on the property case is next month, let us discuss later.", g(["court"])),
    ],
    "s35_whatsapp": [
        ("Sending you a notice under Section 35 BNSS on WhatsApp, you must join the video call for questioning.", g(["police"], i=["notice_s35"])),
        ("This is a notice under Section 41A CrPC, sent on WhatsApp; appear on video call immediately.", g(["police"], i=["notice_s35"])),
    ],
    "s35_lawful": [
        ("A notice under Section 35 BNSS has been served at your residence; appear at the police station.",
         g(["police"], i=["notice_s35"], d=["appear_in_person"])),
    ],
    "summons_attached": [
        ("The summons issued by the court is attached for your information.", g(["court"], i=["summons_court"])),
        ("Please find the court e-summons attached.", g(["court"], i=["summons_court"])),
    ],
}
