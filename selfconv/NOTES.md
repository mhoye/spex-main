## development notes

I'm keeping the self-schema.py and elf2self code here with the SPEX
work separated because it's nice to have them to test with. This may
change eventually, or my own work will be discarded in favor of
compartmentalizing change managment tools. 

I think that's the decision I need to make in this folder; is there
a basic ".spex" file format I want that's better than .self in some
way or do I want to do something like, have something comparable to
getters and setters for every extension to .self files and have
them be separate?

While I'm still experimenting, I'm inclined towards the former. 

I want to be able to let both live side by side, so that means spex
gets its own parallel system. 

- mhoye, Oct2026
