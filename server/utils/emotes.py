import random
import re


default_speech_tone = [
    ("{verb}", "{verb}")
]
speech_tones = {
    ":\)$": [
        ("smile and {verb}", "smiles and {verb}"),
        ("smilingly {verb}", "smilingly {verb}")
    ],
    ":\($": [
        ("frown and {verb}", "frowns and {verb}"),
        ("gloomily {verb}", "gloomily {verb}")
    ],
    ":D$": [
        ("laugh and {verb}", "laughs and {verb}"),
        ("chuckle and {verb}", "chuckles and {verb}")
    ]

}

default_speech_verb = [
    ("say", "says"),
]
speech_verbs = {
    "\?$": [
        ("ask", "asks"),
        ("wonder", "wonders"),
        ("inquire", "inquires")
    ],
    "!(!$)": [
        ("shout", "shouts"),
        ("scream", "screams"),
    ],
    "!$": [
        ("exclaim", "exclaims"),
        ("declare", "declares")
    ],
    "(~$)": [
        ("whisper", "whispers"),
        ("mutter", "mutters")
    ]
}


def emote_converter(text):
    """
    Adds various emotions to a text string
    :param text: Unformatted text string
    :return: Tuple containing text, tone and verb
    """
    text = text.strip()

    # Determine the tone
    tone = None
    for tone_key, tones in speech_tones.items():
        match = re.search(tone_key, text)
        if match:
            text = re.sub(tone_key, "", text)
            tone = random.choice(tones)
            break

    # It rhymes :D
    if tone is None:
        tone = random.choice(default_speech_tone)

    # Determine the main verb
    text = text.strip()
    verb = None
    for verb_key, verbs in speech_verbs.items():
        match = re.search(verb_key, text)
        if match:
            if len(match.groups()):
                text = re.sub(match.groups()[0], "", text)

            verb = random.choice(verbs)
            break

    if verb is None:
        verb = random.choice(default_speech_verb)

    return text, tone[0].format(verb=verb[0]), tone[1].format(verb=verb[1])


