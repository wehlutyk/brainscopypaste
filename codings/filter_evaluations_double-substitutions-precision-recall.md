Double-substitutions filter precision-recall analysis
=====================================================

Codings for section 4.2 of notebooks/filter_evaluations.ipynb.

The codings are as follows:
tp: true positive
tn: true negative
fp: false positive
fn: false negative


Sample from kept and non-kept substitutions
-------------------------------------------

The counts are:
false negatives: 4
false positives: 2
true negatives: 89
true positives: 3

Conclusion:
precision: .6
recall: .429

Substitution number	Coding
001			tn
002			tn
003			tn
004			tn
005			tn
006			tn
007			tn
008			fn
009			tn
010			tn
011			tn
012			tn
013			tn
014			tn
015			tn
016			tn
017			tn
018			tn
019			tn
020			fn
021			tn
022			tn
023			tn
024			tn
025			tn
026			tn
027			tn
028			tn
029			fp
030			fp
031			tn
032			tn
033			tn
034			tn
035			tn
036			tn
037			tn
038			tp
039			tn
040			tn
041			tn
042			tn
043			tn
044			tn
045			tn
046			fn
047			tn
048			tn
049			tn
050			tn
051			tn
052			tn
053			tn
054			tn
055			tn
056			tn
057			tn
058			tn
059			tn
060			tn
061			tp
062			tn
063			tn
064			tn
065			tn
066			tp
067			tn
068			tn
069			tn
070			tn
071			tn
072			tn
073			tn
074			tn
075			tn
076			fn
077			tn
078			tn
079			tn
080			tn
081			tn
082			tn
083			tn
084			tn
085			tn
086			tn
087			tn
088			tn
089			tn
090			tn
091			tn
092			tn
093			tn
094			tn
095			tn
096			tn
097			tn
098			tn
099			tn
100			tn


Sample from only kept substitutions
-----------------------------------

The counts are:
false positives: 25
true positives: 75

Conclusion:
precision: .75

Substitution number	Coding
001			tp
002			tp
003			tp
004			tp
005			fp
006			fp
007			tp
008			tp
009			fp
010			tp
011			tp
012			tp
013			tp
014			tp
015			tp
016			tp
017			tp
018			tp
019			tp
020			fp
021			fp
022			fp
023			tp
024			tp
025			tp
026			fp
027			tp
028			tp
029			fp
030			tp
031			tp
032			tp
033			tp
034			tp
035			tp
036			tp
037			tp
038			tp
039			tp
040			tp
041			fp
042			tp
043			fp
044			tp
045			tp
046			tp
047			tp
048			fp
049			fp
050			tp
051			tp
052			tp
053			tp
054			tp
055			fp
056			tp
057			fp
058			tp
059			tp
060			tp
061			tp
062			tp
063			tp
064			tp
065			tp
066			fp
067			tp
068			tp
069			fp
070			fp
071			tp
072			tp
073			tp
074			tp
075			fp
076			tp
077			tp
078			tp
079			tp
080			fp
081			tp
082			fp
083			tp
084			fp
085			tp
086			tp
087			fp
088			tp
089			tp
090			tp
091			tp
092			tp
093			fp
094			tp
095			fp
096			tp
097			tp
098			fp
099			tp
100			tp
