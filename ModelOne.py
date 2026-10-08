import os
import requests

# Endpoint of the System One API (typed answers, no free text)
API_URL = "https://api.codiv.ai/v1/systemone"

API_KEY = os.environ["CODIV_API_KEY"]

# Models to compare: 4 text-only ones + OpenJev
MODELS = ["laya-1.0", "verdict-1.4", "clm-v0.1", "jevk5-0.2", "openjev-latest"]

# The text the model will "read" (called "state" in the API)
EMAIL = (
    "Subject: URGENT - Your account will be suspended\n"
    "Dear customer, we detected suspicious activity. Verify your identity "
    "within 2 hours at http://secure-bank-login.xyz or your account will "
    "be blocked."
)

# The "form" the model has to fill in.
# Each key (is_phishing, email_type, risk) is an ID we choose;
# the answers come back under the same IDs.
QUESTIONS = {
    
    # NOUL = yes/no question.
    # Returns a probability between 0 and 1 .

    "is_phishing": {
        "type": "noul",
        "instructions": "Is this email a phishing attempt?",
    },

    # CHOICE = pick one option from a list we define.
    # Returns the winner, the probability of every option and a confidence value.
    # Tip: keep options clearly different from each other, overlapping options
    # split the probability and lower the confidence.
    "email_type": {
        "type": "choice",
        "instructions": "What kind of email is this?",
        "criteria": {
            "phishing": "Asks to verify an account or credentials via a link, with urgency",
            "bec": "An executive or vendor asks for a wire transfer or payment",
            "spam": "Unsolicited ads or promotions",
            "legitimate": "Normal email with no malicious intent",
        },
    },

    # SCORE = place the text on a scale we define.
    # The list order matters: index 0 is the lowest level, the last one the highest.
    # Returns a number between 0 and N-1.
    "risk": {
        "type": "score",
        "instructions": "How risky is this email?",
        "criteria": [
            "No risk",        
            "Low risk",       
            "Medium risk",   
            "High risk",      
            "Critical risk",  
        ],
    },
}


def ask(model, state, questions):
    #Send a text + typed questions to one model and return its answers.
    #model:     model ID
    #state:     the text to analyze
    #questions: dict of questions
    resp = requests.post(
        API_URL,
        headers={
            # Bearer token authentication with our API key
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        # Request body: which model, what to read, what to answer
        json={"model": model, "state": state, "questions": questions},
        timeout=60,  # don't wait forever if the server is slow
    )
    # Raises an exception on HTTP errors (401 bad key, 429 rate limit, 5xx...)
    resp.raise_for_status()

    # The response has "answers" keyed by our question IDs (plus "usage" info)
    return resp.json()["answers"]


if __name__ == "__main__":
    # Run the same email through every model so we can compare them
    for model in MODELS:
        # try/except so one failing model doesn't stop the whole comparison
        try:
            answers = ask(model, EMAIL, QUESTIONS)

            # Pull out each answer by the ID we chose in QUESTIONS
            p_phishing = answers["is_phishing"]["noul"]  
            email_type = answers["email_type"]          
            risk = answers["risk"]                       

            print(f"\n=== {model} ===")
            print(f"Phishing? {p_phishing:.1%}")

            # "confidence": 1 = one option has all the probability,
            #               0 = all options equally likely.
            # It is NOT the chance of being right, only how decided the model is.
            print(f"Type: {email_type['choice']} (confidence {email_type['confidence']:.2f})")

            # Probability of every option (they add up to 100%)
            for option, prob in email_type["probabilities"].items():
                print(f"   {option}: {prob:.1%}")

            print(f"Risk: {risk['score']:.2f} / 4 (confidence {risk['confidence']:.2f})")

            # Decision rule: only automate when the model is both sure it's
            # phishing AND decided about the type. Otherwise a human decides.
            # Tune these thresholds after testing with emails you already know.
            if p_phishing > 0.9 and email_type["confidence"] > 0.7:
                print("-> Block and open ticket automatically")
            else:
                print("-> Manual review")

        except Exception as e:
            print(f"\n=== {model} ===\nERROR: {e}")