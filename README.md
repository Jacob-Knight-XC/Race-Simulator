# Race-Predictor
 Stores all the files for a program that will pull data from TFRRS to predict the outcome of a race.

Steps to Complete
1. Get a Database with all d3 athletes, teams, and racetimes using scrapy (Done)
2. Make a program that can pull the data from the Database 
3. Create algorithms to help accuraltely predict a race time using an
athletes latest race results. Plus a course rating and what that does to a time.
4. Make a user interface using streamlit that can show a team or athletes
results after making an input. 
5. Create the first mode of a single athlete race.
6. Create the second mode of a team race.
7. Start to add more things to make it more accurate. 
8. Add a compare mode that will compare my simulation to the actual results
of a race.


User Stories:

How the user will interact with my program. 
This will be a web-based program that users will be able to put in certain inputs 
then run a similation that will predict the outcome of a race. 

Story One:
Connor wants to know what could happen in a race between 10 certain athletes.
He goes to my program through streamlit and starts it up. He begins first by 
selecting one of the two modes. A team race or an individual race. He chooses
individual race. From there it will ask how many people he plans to put into
the race. He chooses 10. Then it will give 20 drop downs in 2 rows where he first will 
select the team of the athlete he wants. Then the second row is where he will 
select the specific athletes he wants to race. Once all athletes are chosen he 
will move on to the last part. Here he will pick a number 1-5 to show the course
toughness. 1 being a very easy fast course and 5 being a very hard slow course.
From here he will then be able to simulate the race by hitting the simulate button
This will give him a list of the ten athletes he chose and use algorithms to predict
a race between them. It will show a time range of what they will probably run and 
show the probability of them finishing in there current place. 

Story Two:
Aiden wants to know what could happen in a race between 5 certain teams. 
He goes to my program through streamlit and starts it up. He begins first by 
selecting one of the two modes.A team race or an individual race. He chooses
team race. From there it will ask how many teams he plans to race. He chooses 
5. Then it will give 5 drop. This is where he will pick what five teams he wants
to race. Then he will pick a number 1-5 to show the course toughness. 1 being 
a very easy fast course and 5 being a very hard slow course. Then he will hit
simulate to show the race results. From here it will give two tables. The first
will be the teams in order of who would win and what there average points would
be as well as there percentage to finish in there current place. The next table
would show the individual results of all the athletes that are within the 5
teams. This would also show there race time range and the percentage to finish
in there current spot. 
