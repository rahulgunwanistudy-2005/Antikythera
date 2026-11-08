"""Versioned category lexicon. Scores measure text similarity, not validity."""
VERSION='organ-system-lexicon-2026-11-07-v1'
LEXICON={
'urinary':'urine urinary stone stones gravel bladder kidneys kidney dropsy strangury diuretic water retention',
'gi':'stomach bowels belly digestion indigestion diarrhoea diarrhea flux dysentery colic wind vomiting liver jaundice spleen cholic',
'skin':'wound wounds ulcer ulcers sore sores burn burns skin scab itch itching rash fistula bruise bruises swelling swellings',
'respiratory':'cough coughs lung lungs asthma breath breathing phlegm catarrh throat hoarseness consumption',
'neuro':'pain pains headache headach migraine epilepsy falling sickness palsy apoplexy lethargy sleep sleeping nerve nerves memory convulsion convulsions',
'joint':'gout podagra rheumatism joint joints sciatica inflammation arthritis',
'cardiovascular':'heart pulse palpitation palpitations blood pressure cardiovascular fainting',
'metabolic':'diabetes thirst thirsty frequent urination glucose sugar',
'gynaecological':'womb mother menstrual menstruation terms menses childbirth child-birth labour labor birth milk breasts women barren barrenness',
'infection':'fever fevers ague agues infection infectious pestilence plague measles smallpox worms worm',
'eye':'eye eyes sight vision ophthalmia eyelids blindness',
'poison':'poison poisonous poisoned venom venomous antidote snake serpent bite bites bitten mad dog'
}
# Explicit historical phrases used to propose exact source spans.
PHRASES={k:sorted(set(v.split()+(['falling sickness'] if k=='neuro' else [])+(['yellow jaundice'] if k=='gi' else [])),key=lambda x:(-len(x),x)) for k,v in LEXICON.items()}
