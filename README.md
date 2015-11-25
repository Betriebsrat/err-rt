# err-rt

Fork of https://github.com/jwm/err-rt.git  

New features:   

* Returns "newbodies" (Tickets with Status = 'new' and owner = 'nobodies')
* Possibility to mark tickets as spam ( Need to adjust the CustomField probably )
* Possibility to change ticket owners 
* Writes a comment (action report) to given ticket about the changes, this is useful if you got a dedicated bot user for remote controlling RT

Interfaces [errbot](https://github.com/gbin/err) with [Request
Tracker](http://www.bestpractical.com/rt/).


## Installation

```
!repos install https://github.com/Betriebsrat/err-rt.git
```


## Commands

Emits summary information about a ticket when it's mentioned.

<@jwm> coworker: have you seen rt 42424?  
< errbot> RT 42424: Something bad happened (open) in General, owned by jwm (https://rt.example.com/42424)   

Plus:   

* !rt give - Sets a new owner for a ticket. Usage: !rt give <id> <owner>
* !rt newbodies - Prints out all tickets with status 'new' and owner 'nobody'. Usage: !rt newbodies
* !rt search - "Searches through all ticket queues for given subject. Output limited to 3 items. Usage: !rt search <subject>
* !rt spam - Closes ticket and sets custom SPAM field to true. Usage : !rt spam <id>