Single-substitutions filter precision-recall analysis
=====================================================

Codings for section 4.1 of notebooks/filter_evaluations.ipynb.

The codings are as follows:
```
tp: true positive
tn: true negative
fp: false positive
fn: false negative
```


Sample from kept and non-kept substitutions
-------------------------------------------

The counts are:
```
false negatives: 5
false positives: 0
true negatives: 84
true positives: 11
```

Conclusion:
```
precision: 1
recall: .688
```

```
Substitution number	Coding
001			tn
002			tn
003			tn
004			fn
005			tn
006			tn
007			tn
008			tn
009			fn
010			tn
011			tn
012			tn
013			tn
014			tn
015			tn
016			tn
017			tp
018			tn
019			tn
020			tn
021			tn
022			tn
023			fn
024			tn
025			tn
026			tn
027			tn
028			tn
029			tn
030			tn
031			tn
032			tp
033			tn
034			tn
035			tn
036			tn
037			tn
038			tn
039			tn
040			tn
041			tn
042			tn
043			tn
044			tn
045			tn
046			tn
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
061			tn
062			tn
063			tn
064			tn
065			tn
066			tn
067			tn
068			tn
069			fn
070			tn
071			tn
072			tn
073			tp
074			tp
075			tp
076			tp
077			tp
078			tn
079			tp
080			tn
081			tn
082			tn
083			tp
084			tp
085			tn
086			tn
087			tp
088			tn
089			tn
090			tn
091			tn
092			fn
093			tn
094			tn
095			tn
096			tn
097			tn
098			tn
099			tn
100			tn
```


Sample from only kept substitutions
-----------------------------------

The counts are:
```
false positives: 13
true positives: 87
```

Conclusion:
```
precision: .87
```

```
Substitution number	Coding
001			tp
002			tp
003			tp
004			tp
005			tp
006			tp
007			tp
008			tp
009			tp
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
020			tp
021			fp
022			tp
023			tp
024			tp
025			tp
026			tp
027			tp
028			tp
029			tp
030			tp
031			fp
032			tp
033			tp
034			fp
035			tp
036			tp
037			tp
038			tp
039			tp
040			tp
041			tp
042			tp
043			tp
044			tp
045			tp
046			tp
047			tp
048			tp
049			tp
050			fp
051			tp
052			fp
053			tp
054			tp
055			tp
056			tp
057			fp
058			fp
059			tp
060			tp
061			tp
062			tp
063			tp
064			tp
065			tp
066			fp
067			fp
068			tp
069			tp
070			tp
071			tp
072			tp
073			tp
074			tp
075			fp
076			fp
077			tp
078			tp
079			tp
080			tp
081			tp
082			tp
083			tp
084			tp
085			tp
086			tp
087			fp
088			tp
089			tp
090			tp
091			fp
092			tp
093			tp
094			tp
095			tp
096			tp
097			tp
098			tp
099			tp
100			tp
```
