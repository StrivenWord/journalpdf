---
title: "Authoring Educational Hypercomics assisted by Large Language Models"
authors:
  - "Valentin Grimm"
  - "Jessica Rubart"
affiliations:
  - "Hochschule Ostwestfalen Lippe University of Applied Sciences, Lemgo"
doi: "10.1145/3648188.3675124"
date-published: "2024-09-10"
date-extracted: "2026-04-04"
---


# Authoring Educational Hypercomics assisted by Large Language

Models

Valentin Grimm

valentin.grimm@th-owl.de

# OWL University of Applied Sciences and Arts

Hoxter, Germany

ABSTRACT

Interactive stories can be an effective approach for teaching purposes. One shortcoming is the effort necessary to author and create

these stories, especially complex storylines with choices for the

readers. Based on recent advances in Natural Language Processing

(NLP), new opportunities arise for assistance systems in the context of interactive stories. In our work, we present an authoring

approach and prototypical tool for the creation of visual comic-strip

like interactive stories, a type of hypercomics, that integrate an

Artificial Intelligence (AI) assistance. Such comics are already used

in our Gekonnt hanDeln web platform. The AI assistance provides suggestions for the overall story outline as well as how to design

and write individual story frames. We provide a detailed description

about the approach and its prototypical implementation. Further-

more, we present a study evaluating the prototype with student groups and how the prototype evolved in an iterative style based

on the students' feedback.

# CCS CONCEPTS

* Applied computing - Hypertext / hypermedia creation; In-

teractive learning environments; Media arts; * Information sys-

tems - Language models; Recommender systems; * Comput-

ing methodologies - Natural language generation; * Human-

centered computing - HCI theory, concepts and models.

# KEYWORDS

Storytelling, Authoring, GPT, Hypercomics, Large Language Models



Valentin Grimm and Jessica Rubart. 2024. Authoring Educational Hypercomics assisted by Large Language Models. In 35th ACM Conference on Hypertext and Social Media (HT '24), September 10-13, 2024, Poznan, Poland.

# 

# INTRODUCTION

Interactive narratives have a long history in the digital era. For

example, interactive fiction works, also known as "text adventures",

are considered games, but also narratives, and have been introduced as early as 1977 with works like "Adventure" or "Dungeon" (aka

"Zork") [ 11]. Users are presented with textual information about a simulated world and have to make decisions to shape a story.

This work is licensed under a Creative Commons Attribution-NoDerivs International

HT '24, September 10-13, 2024, Poznan, Poland

(c) 2024 Copyright held by the owner/author(s).

# 

https://doi.org/10.1145/3648188.3675124

Jessica Rubart

jessica.rubart@th-owl.de

# OWL University of Applied Sciences and Arts

Hoxter, Germany

They can type input in natural language to influence the ongoing

narrative. "Solving" such a work requires a comprehensive under-

standing of the simulated world. Storytelling has been recognized

as a learning activity. Therefore, interactive narratives can be found in the context of education. For example, Smith et al. [ 19] present

several examples of "decision stories" to teach adolescents about making good decisions for their health. Petousi et al. [ 14] use in-

teractive stories for history education in a collaborative remote

scenario of adolescent students. In the context of our project "Gekonnt hanDeln" 1, we have de-

veloped a web platform that offers free resources to train privately

employed domestic workers [ 6]. The platform uses different kinds of media, such as quizzes, videos, and in particular a special kind of

interactive stories, i.e. educational hypercomics. With that, users join fictional characters at work and help them to make the right

decision in challenging situations. The stories are presented in a comic-strip like way. Users can advance the comic and may come across a decision situation. There is an ongoing debate about the definition of the term comic in the digital context. In this work we refer to digital comics as linked digital comics, as defined by Rizzi [ 15]. Linked digital comics are characterized by visualizing one part of the comic at a time while hiding the rest of it. More particularly, our concept is focused on hypercomics in the form of a branched narrative (cf. Goodbrey [ 5]) where one "panel" (i.e. node/frame) is

shown at a time. . According to Wu et al. [ 20], educational digital storytelling can

offer potentially a number of different learning outcomes, including

the strengthening of critical thinking, self-awareness and awareness

of others, learning attitudes and emotional engagement and several

more. This shows the potential of digital storytelling.

# Especially hypercomics, where users control the outcome and

storyline, can become complex. By increasing the number of choices for users, the complexity and number of paths grows compared to a normal story or video course that has a direct and linear path.

However, artificial intelligence (AI) technology that is growing at an extraordinary pace, especially in the field of natural language

processing (NLP), promises to make authoring stories much easier

(cf. [ 9]). Such technology, therefore, creates new opportunities for

simplifying the task of authoring hypercomics for educational pur-

poses by integrating domain-specific large language models (LLMs)

into the process. In this paper, we present an approach and a prototypical creative

support tool for authoring educational hypercomics. The focus is

on an LLM-driven AI-assistance. Although the term "assistance" is also used in the context of support for people with disabilities, in our project we use the term to describe an AI support augmenting

authors of educational hypercomics. The resulting stories can be

1 "Gesund und kompetent in haushaltsnahen Dienstleistungen" (in German)

integrated seamlessly into our Gekonnt hanDeln training platform.

We evaluated the tool iteratively with three different groups of students and optimized it for the next evaluation group based on

the students' feedback. The story creation is based on story frames. A story frame is a hypertextual node that can be linked to other frames to build the overall story. It consists of a background image, character im-

age, speech bubble, and optional decision buttons, which mark

decision paths. The decision paths create parallel story lines with

different outcomes. Besides suggestions for the story outline, the

AI-driven assistance provides text suggestions for each story frame and guidance for the character and environment images, as well as

potential decision points. Overall, our approach aims to facilitate a

human-centered writing process supported by an LLM. From this

perspective, our contribution in this paper is fourfold:

* An approach and prototypical creative support tool to author

educational hypercomics assisted by large language models

* The designed prompt engineering approach for specializing

the language model for educational hypercomics

* A study delivering first usage feedback regarding the quality

of the AI assistance

* Learnings and results from the iterative and user-centered

development process

In the next section, we compare our approach to related work.

# Afterwards, the AI-assisted authoring approach of educational hy-

percomics is described in detail. Section 4 presents the prototypical

implementation of our authoring approach as well as its incremen-

tal improvements based on feedback of different student groups.

Section 5 describes the evaluation with three different groups of

students. Afterwards, we discuss results and limitations. The paper

ends with conclusions and future work.

# RELATED WORK

There are many papers in the context of automatic story generation. A very recent paper by Xie et al. [ 21] compares state-of-the-art

techniques for automatic story generation with the LLM GPT-3 2

in conjunction with prompt-based learning for domain specification. Kelly et al. [ 9]. They discuss the pressure on creatives due

to the emerging capabilities of AI-driven narrative systems, their

opportunities, but also their limitations, in particular controllability

and explainability. They propose and discuss systems to combine

language models and narrative planning aiming at human-centric authoring tools. Atzenbeck et al. [ 1] discuss suggestion nodes in the

context of the spatial hypertext system Mother. These are intended

to stimulate user creativity. Suggestions are derived from knowl-

edge bases, whereby ChatGPT is integrated through a machine-

generated knowledge base.

Collaborative writing with AI systems based on neural networks has been discussed earlier by Nichols et al. [ 13] from a different

perspective. They show that alternating between human and AI

system in an incremental story writing process can improve the overall story quality compared to a fully AI authored story. Contrarily, Zhao et al. [ 25] make the observation that fully AI-authored

stories outperform those, collaboratively written in an interleaved

2 developed by OpenAI and basis of ChatGPT

fashion. This contradiction emphasises the fact that this field of

research is not yet sufficiently explored.

One interesting way to leverage the power of AI-driven story creation is to create stories that are neither linear nor simply branching, but create a feeling of limitless possibilities. Yong & Mitchel [ 22] discuss this idea from the perspective of the interactive story

users and observed how their mental models shifted, while explor-

ing the different story lines. There are several historical examples from the context of interactive narratives. Zork [ 11] is an early

example of interactive fiction. The video game Facade builds upon

similar mechanics and adds visual interactions to walk through an

interactive drama [ 10]. These systems utilize rule-based natural

language approaches contrary to foundational LLMs that have a

general world knowledge.

Unlike fully AI-written stories, human-assisted writing through story planning and incremental writing, Yuan et al. [ 23] present an AI-assisted story editor. The editor enables the writing of a story

with several AI-assistance capabilities, such as requesting details about a manually selected section of the text or story seeding, where the AI system provides suggestions to get started with the story. Our work differs from the related work because it discusses an

incremental writing process with very short story snippets and optional AI assistance at any point. In addition, support for visual

components is integrated due to the comic-strip-like character of the stories. In the spirit of Kelly et al. [ 9], we consider AI-driven

support for initial planning of the hypercomic and assistance for

individual frames. Especially the individual frame assistance en-

ables an incremental design process with continuous human-AI

Our approach focuses on human-centered writing of educational hypercomics, which is supported by AI in an interactive way. For this, we are using an LLM and prompt engineering. Hegland [ 8] describes the integration of an LLM in a reading tool so that the reader can ask the LLM regarding some selected text, which can

be considered a human-centered reading process supported by an

# AI-ASSISTED EDUCATIONAL

# HYPERCOMICS

In this chapter, the AI-assisted authoring approach of educational

hypercomics is described. Our approach, inspired by Engelbart's

idea of augmenting human intellect [ 3], targets a human-centered

writing process. It is supported and potentially enhanced by AI-

based recommendations.

In the next section we present the hypertextual story structure

of our educational hypercomics. Afterwards, we describe in detail how frames and decision points are created in the story design. In the following part, we discuss how we extend the basic system

concept for an optimal integration of LLM-driven assistance. This

section concludes with a usage-example of the presented authoring

Hypertextual Story Structure

A sketch of the hypertextual story structure is depicted in figure

1. It shows the introductory frames (yellow), which are followed by a decision point where the user has to decide how the story

should continue. Green frames represent the "correct" choice and

hypercomics.

red frames represent "wrong" choices. The choices can be nested

arbitrarily. Analogous to Nelson's Xanadu hypermedia model [ 12], permanent IDs are assigned to reusable and linkable units of data, which are story frames as well as their components, i.e. background

and character images, speech text, and decision points. By using a structure model in the system design [ 16], stories are explicitly

assembled from frames. The frames are loosely coupled so that changes to or the further development of stories are easy to handle.

Users can follow the story (frame 1 and 3) and make meaningful

decisions for the story outcomes (frame 2).

# This structure shows that our comic-strip-like interactive learn-

ing stories can be considered digital comics, in particular hypercomics [ 5], as we are showing one frame at a time and the reader can make choices that influence how the story continues. From the

interactivity point of view, Rizzi distinguishes between four types of user agency [ 15], regarding which our comics fit to the more traditional narrative one. One reason for this is that the social target

group in our project, employees in household-related services, pre-

dominantly use simply equipped smartphones. On the other hand, we are currently targeting authors with our AI support, not (yet)

readers. So the resulting comics should not change dynamically based on AI. However, the latter could be interesting for the future.

Story Design User Interface

The hypercomic design User Interface (UI) is illustrated in figure

3 based on the current prototype implementation. The interface is split into four areas: A, B, C and D. Section A is the navigation area where the story creator can choose, create and delete frames. Additionally, if there is an interaction point at the end of the frame list, creators can navigate to a desired story path and jump to the first frame and the frame list of the chosen path. Section B is a

preview of the selected frame from the reader perspective. Creators can position and create the content based on the preview. In case a frame contains an interaction point, the options for the reader can be renamed or deleted inside Section B. Section C is the editor

area, where the creators can choose manipulate the frame content. In this example, they can crop the background image, choose and adapt the character visual, set and adapt the text bubble, as well as add options for the interaction point if the frame is the last in the frame list. Section D allows the creators to start a simulation and

click through the story like a reader would do.

# LLM Assistance UI and Meta Data

To make the suggestion of the LLM assistance meaningful from the start, we added a meta information section (figure 4a) in the GUI where creators can set basic character properties, such as the

work area and character names and personal information about the characters. This is passed to the LLM so that it can generate

meaningful story outline suggestions. These outline suggestions are supposed to help the creators to get started and simplify the ideation process. If creators do not like the suggested story outline, they can simply let the system regenerate it as many times as they like until it is satisfactory. Alternatively, they can make their own adjustments to a suggested story outline or enter their own one. For the assistance in the story creation process, we propose a suggestion panel in section C (cf. figure 3). The assistance provides

suggestions for the frame content, such as the speaking person, the place they are at, the text that the person is supposed to say

The story creation area. A: Navigation area; B: Frame preview; C: Editor area; D: Simulation button

(a) Meta information area. Upper area is about general character information. Lower area is about

outline creation.

or a "thought" that allows the LLM to provide context information

additional to the existing information (figure 4b). The "thoughts" can help the creator to get inspiration for the remaining story and set an interaction point. Besides the thoughts, it should be possible

to transfer the suggestions of the assistance into the frame.

Walkthrough Example

To gain a better understanding of the authoring approach and its

main features, we present a walkthrough example, in which an

(b) Examplary recommendation of the

# GPT assistance from the story editor (see

figure 3; added in the editor area)

author (Torsten) creates an educational hypercomic from scratch

with an AI assistance.

Torsten starts his writing process by creating a new story from the entry page. He is uncertain about a specific story and has not yet specified a title. As he works with people in the area of gardening,

he specifies the working field as "gardening". He also provides the names of the characters, which he calls Annette (as employer)

and Karen (as employee). Torsten is well connected with several

employers that privately deploy domestic workers, and he knows one that tends to be emphatically nice (which sometimes leads to

problems). He adds this as a personality trait of Annette in the user

interface. For now, he leaves Karens personal information blank. To get started with the actual story, Torsten clicks on the "gener-

ate recommendation" button to receive an outline recommendation

for his story. The assistance recommends an outline where Karen finds a bag with a significant amount of money in the garden and is torn apart between two main decision strategies. On the one hand, she considers taking the money for herself and hopes that Annette does not know about the money or that she tells Annette about the money. Torsten accepts the outline, but also adds a third option where Karen consults her best friend about the situation. He moves

on with the actual creation process.

To start, Torsten asks the assistance for a recommendation for the first frame. In the recommendation, Karen is located in the garden and enjoys the good weather. For the second frame, the assistance recommends to think about what to do with the money. In this case, the assistance skipped the process of finding the money

in the story and Torsten requests a new recommendation. This

time, the assistance provides a recommendation where Karen finds the money at work. As the recommendation feels too formal for Torsten, he adapts it slightly. He moves on to the next frame where the recommendation is about asking the reader what to do (i.e. keep the money or talk with Annette). Additionally to this recom-

mendations, the assistance added some "thoughts" that outline the

thinking process of Karen, where she is considering advantages and disadvantages of each decision. Torsten keeps those in mind to consider for the remaining story parts. After adding the question in the text field, he adds decision paths for "telling Annette", "keeping

the money" and "consulting her best friend".

First, Torsten wants to complete the path where Karen keeps the money and clicks on the navigation button to move on with that story path. He moves on with writing the comic and each

decision path by working interactively through each frame with

the assistance.

# PROTOTYPICAL IMPLEMENTATION

LLM Assistance System Architecture

An overview of the assistance's system architecture based on the

current prototype implementation is depicted in figure 5. We de-

veloped a web application (app) using the Python web framework

Flask [ 7]. The backend provides two hypertext transfer protocol

(HTTP) endpoints as an application programming interface (API)

to the client. One endpoint provides the respective story outline

recommendation, and the other endpoint provides the respective

frame recommendation. For the development of the prompts, i.e. the instructions to the LLM, and the interaction with the LLM, we used the LangChain framework [ 2]. In the user evaluations (cf. section

5), we used the LLM GPT-3.5-Turbo and version "2023-05-15". For the outline recommendation, the author or creator of a story only needs to provide the meta information which, in turn, is integrated into a prompt (see tab. 1 & 2). Additionally, formatting

instructions are provided in the prompt. Based on the constructed

prompt, the LLM provides a story outline recommendation that is formally split into two parts as requested in the prompt: An outline of the story (e.g. the babysitter is asked to stay longer than planned due to unforeseen events) and a decision point, where the character

interacting with the client.

(view taken by the reader) has to make a decision (e.g. stay longer

or risking a disagreement by insisting to leave as planned).

For the frame recommendation, the meta information, the story outline as well as the story history are used to construct a prompt for the LLM (see tab. 1 & 2). Additionally, it is possible that the creator specifies a character that is supposed to speak in the frame at hand. This is not mandatory. The story outline is provided in a single string with the outline and decision point combined. The story history is provided as a list of strings ordered by occurrence, where each string is the text spoken in each individual historical

frame. There is not yet information about characters or places provided in the story history as they are not textually described by the creators, but provided in the form of images. This is an

important improvement point for future versions of the prototype. In order to handle long stories and reduce the prompt size, we

implemented a "summary memory" that will utilize the LLM to summarize the story history if it becomes too long (> 1000 tokens). When the summary of the history is conducted, the last two text

snippets are conserved to provide immediate context to the LLM

and avoid "hard cuts" in the recommendations. One specialty of the system is the "thoughts" output of the frame

recommendation. Although we did not specify it in the format

instructions, the LLM sometimes adds an additional string after

the formatted response that contains additional information about the context of the frame, e.g. what direction the LLM envisions to

move towards with the current frame recommendation. While this behaviour was not desired at first, we believe that it can provide valuable guidance to the creators. Therefore, we kept it and provided it to the creators tagged as "thoughts" (cf. figure 4b). In future work,

this should be implemented explicitly to increase reliability.

# Incremental Improvements between

Evaluations

We evaluated the prototypical implementation with three student groups (cf. section 5). Based on the feedback of each student group,

we improved the system incrementally. With respect to the evaluations, this means that each student group had a slightly different

system to work on.

The initial system did not provide story outline suggestions. For

the second increment, we added the story outline suggestions by

outline recommendation (translated from German)

Outline Recommendation Prompt I write interactive stories with an editor I developed myself. The editor is designed to create stories in which two people interact. The context of the stories are privately employed domestic workers such as cleaners or

gardeners. The employees interact with the employer due to unforeseen or foreseeable events and find themselves in a situation where they have to make a difficult decision about how to proceed. Can you create some creative story outlines for me for such interactive stories in German? - The scenario takes place in the context of the following activity: {workArea} - The employer is called: {employer}. The following is known

about this person: {employerInfo} - The domestic worker is called:

employee. The following is known about this person: {employeeInfo} Please create a creative story outline for such an interactive story. The output should be a markdown code snippet formatted in the following schema, including the leading and trailing ""'json" and ""'": "'json { "Outline": string // A suggestion for the outline of the story. 30 - 50

words. "Decision point": string // Explanation of the story's decision

point. Approximately 30 words. } "'

frame recommendation (translated from German)

Frame Recommendation Prompt You write an interactive story in which a scenario of privately employed

domestic workers with the following characteristics is described: - A maximum of two characters interact with each other - The scenario takes place in the context of the following activity: {workArea} - The employer is called: employer. The following is known about this person:

{employerInfo} - The domestic worker is called: employee. The following is known about this person: {employeeInfo} - The story is embedded in the following context: {outline} - The same person can say several sections of text in a row - The story serves to educate the domestic worker - The aim is to create a well-rounded story that is introduced and leads to a decision scenario (choice between three options) for the domestic worker - After the decision, the story is led into the final section. Enter a single paragraph of text, the name of the character and the location where the character is located to start the story. The output should be a markdown code snippet formatted in the following schema, including the leading and trailing ""'json" and ""'": "'json { "character name": string // The first name of the character. "role": string // The character's role in the story. "Text": string // The section of text said by

the character. Maximum one sentence and 50 characters. "Location": string // The location where the character is located. } "' The story so far can be summarised as follows: {summary} The last two statements

are: {last_messages} The text section is spoken by {character_choice}.

GPT in the system to support the authors in their story writing as well as GPT in providing valuable suggestions from the start. After the second user study, we updated the functionality on how the

input data for the frame suggestions are preprocessed by increasing the summary threshold from 200 tokens to 1000 tokens and always providing the last two text snippets in clear text. Additionally, we

added the option to specify the character that is supposed to speak

in the current frame.

# EVALUATION

To evaluate the application, we surveyed three different groups of students in the winter semester 2023/24 to avoid bias from previous sessions. First, the students were introduced to the use case of

interactive stories and provided with examples from our gekonnt-

handeln.de platform. Then, they got an introduction into the story creation tool. Lastly, they were provided with credentials to try the tool online and create their own stories. They were instructed to create the stories in groups of two. The groups had about an hour

to write the stories.

Students in the first student group (group 1) study Sociology

(bachelor) and did the evaluation in a course on communication

strategies. All 8 participants were women. The second (group 2)

and third (group 3) student groups study applied computer science in the third and fifth semester, respectively. The second group did the evaluation in the context of a course on business computer

sciences (third bachelor semester) and consisted of 1 woman and 6 men. The third group did the evaluation in the context of their business intelligence course and consisted of 1 woman and 7 men. All students were between 20 and 25 years old (we did not ask for

individual ages).

After the students have created their stories, they answered

a short survey with the questions listed below (translated from German). Questions 1.x and 2.x are scored based on a likert scale from 1 (fully disagree) - 5 (fully agree). Questions 2.5 and 2.6 were not implemented for the first group as their version of the system

did not include the respective functionality. Questions 3.x had four possible answers: worse (0), even (1), slightly better (2) and much better (3). Question 3.2 was added for groups 2 and 3 based on

feedback from group 1.

- Q1.1: Was the application overall easy to understand?

- Q1.2: Was the application overall easy to use? - Q1.3: Did you have a good overview of your story as it

- Q1.4: Did you find it easy to adjust characters, speech

bubbles, and response options (position, size, ...)

* Perceived GPT performance:

- Q2.1: Were the text, location, and character suggestions

from ChatGPT relevant to your story? - Q2.2: Did the "thoughts" of ChatGPT assist you in creating

- Q2.3: Were the pieces of information you provided to Chat-

# GPT meaningfully incorporated into the recommenda-

- Q2.4: Could you provide ChatGPT with all the information

necessary for the story through the provided fields?

- Q2.5: Were the outline suggestions from ChatGPT helpful

for your story?

- Q2.6: Were you motivated to continue writing the story

to see what suggestions ChatGPT would make next?

* Comparison of GPT and non-GPT assisted application:

- Q3.1: Make an estimate: How much did the recommen-

dations from ChatGPT speed up the development of the

- Q3.2: Make an estimate: How much did the ChatGPT rec-

ommendations improve the quality of the comics?

* General remark: - Take some time and write down which features you felt

were missing in the application. Specifically, what addi-

tional interaction options would you like with the recom-

mendation system?

Note that the word "ChatGPT" is technically incorrect (we used

GPT-3.5 turbo). The wording was chosen because "ChatGPT" is widely known, while GPT-3.5 turbo is a rather technical less well

In addition to the survey, we collected usage data and tracked if and when users used a recommendation (story outline or frame) in

their story and when they manually wrote the frame text/outline. Based on the survey and oral feedback, we improved each version

of the app as highlighted in section 4.2

Results & Discussion

The results from the survey are displayed in figures 6 (usability),

8 (perceived GPT performance) and 7 (comparison of GPT and

non-GPT editor). Although, the user groups were rather small and might not allow

for conclusive findings, we believe that some interesting patterns should be discussed. With respect to the usability questions, we can observe a slight degradation over the three groups. This is strange

as the app was improved in-between the sessions. Therefore, the reason for the degradation might lie in the heterogeneity of the

three groups and show how critical the different student groups were towards the application. While the students from the field of

sociology might have been influenced by their perceived high value of the resulting stories for the readers, the other student groups

might have been more concerned with the technicalities behind the

editor and, therefore, more critical towards it.

With respect to the survey questions concerning the GPT recommendations (figures 8 and 7), we can notice that the degradation over the three sessions is not observable. Instead, it is observable that group 2 provided the worst feedback in all categories besides 2.6 and 3.2 and group 3 gave the best feedback on all questions besides 2.6 and 3.2 with a median of at least 1 higher. Group 1 provided feedback in the middle range, but an analysis of the usage data

(figure 9) shows that this group used the recommendations very

sparingly, again indicating a strong positivity bias. This behavior

is partially rooted in the fact that, especially, initial recommendations were of lower quality. Among others, this encouraged us to

add a story outline and outline recommendations in the second

iteration and to improve the outline recommendations in the third iteration. With respect to the usage data, we can also see that the usage of the GPT recommendations is highest in relation to the manually written texts for group 3. This is in alignment with the user feedback. Generally, group 2 was much less eager to use the

recommendations compared to manually written texts, again in

agreement with the survey feedback. In direct comparison between

groups 2 and 3, especially questions 2.4 (utilization of provided

information by GPT), 2.5 (helpfulness of outline suggestions), and

3.1 (speed compared to non-assisted app), and the oral feedback

show that mostly the improved context summarization contributed to a better user experience with respect to the LLM assistance. In addition, the update for group 3 allowed the creators to specify the

character for a frame recommendation.

# DISCUSSION & LIMITATIONS

The prototypical implementation of the story editor presented has been generally perceived as a valuable tool for the creation of educa-

tional hypercomics with an LLM assistance. Therefore, our designed

approach was perceived as meaningful. The data further suggests

that our updates between the evaluation sessions have been per-

ceived as improvements over the previous versions with respect to

the LLM assistance. In particular, the improved story outline rec-

ommendations have been beneficial. One important shortcoming of our study is that we have created a prototypical custom tool for

creating the hypercomics. This introduced usability obstacles that

might have hindered feedback with respect to our LLM assistance. For example, some users did not realize that they could specify the

character for whom the frame recommendation is generated. Moreover, it is important to note that we have done a preliminary study with small user groups. The first group has been very different to the second and third groups with respect to gender proportions and the field of study. Looking at the feedback from the other two

groups a rather strong positivity bias must be considered with

respect to the first group.

In general, our approach targets at facilitating a human-centered

writing process supported by an LLM. Our study, although limited,

confirms that an LLM assistance is perceived as valuable support.

We did not explore the question whether fully AI-authored sto-

ries can outperform those written with LLM assistance. From our perspective in our project, focusing on a social target group, it is

crucial to include human narrative planners. But the combination

of artificial and human intelligence can boost the performance of

writing. In Shneiderman's human-centered artificial intelligence

(HCAI) framework [ 18] human control and computer automation are two design dimensions. In our setting we can achieve both - appropriate human control as well as a good level of automation.

# CONCLUSION & OUTLOOK

In this work, we have presented an innovative authoring approach

for the creation of comic-strip-like interactive learning stories, i.e.

hypercomics, with LLM assistance. More specifically, based on a

user-driven design process, we have worked out valuable features for such systems. It is valuable to provide an option to generate and

create story outlines before writing the story itself. Moreover, using

an appropriate summarization strategy for the LLM, which considers the most recent story snippets in plain text, is vital to generate

meaningful recommendations for longer stories. Thirdly, providing

users with "thoughts" alongside the frame recommendations has

been perceived as a meaningful and helpful feature.

For the evaluation and improvement of the story writing experi-

ence, we believe that a guided assessment with individual groups will be most beneficial for future work. The goal is to increase the

users' motivation and reduce distraction through the unclarity of

mendations; Green: Used outline recommendations; Yellow:

# Manually set frames

the UI controls. In particular, it is interesting to dive deeper into

the idea of controllable and explainable text generation and add

closer collaboration-capabilities with the assistance. For example, users might want to ask, why the assistance provided a given rec-

ommendation or make suggestions for additional considerations

when generating a recommendation.

From a more technical perspective, it is desirable to improve the

prompts by adding character and environment information based on the frame so that the LLM is aware of the speakers and environments for each text snippet. Furthermore, the AI support can be

extended to the images themselves to generate them as recommendations for the authors. To make prompts more dynamic and make

domain-knowledge by the LLM more nuanced, utilizing retrieval

improvement compared to non-assisting

augmented generation (RAG) is another promising approach (cf.

A particularly interesting aspect of the presented concept are

the "thoughts" of the LLM assistance. Putting stronger focus and

support from a system and/or evaluation perspective might result

in meaningful observations in the context of AI-assisted authoring

of hypercomics. In addition, it can be beneficial to support the creation of a map of a hypercomic and its paths, similar to the collaborative creation of a shared map in reading interactive fiction [ 17]. However, in this case it should be done in collaboration with the AI assistance and

optionally working together with co-authors. Activity awareness [4], then, needs to be extended to include the system as an actor. For the future it is also interesting to consider AI support for the readers. For example, in Rizzi's social agency [ 15] readers are a kind of co-authors, for whom AI support can also be beneficial.

Finally, the authoring approach can be further enhanced by allowing the authors to integrate dynamic AI support for the readers, i.e. to let specific story paths automatically adapt when the reader

selects those. Here, human control and explainability would be

# The frontend and gpt-code implementation is openly available

at https://github.com/GrimmV/story_editor and

https://github.com/GrimmV/story_editor_gpt (including the origi-

nal German prompts).

ACKNOWLEDGMENTS We would like to thank the German Federal Ministry of Education

and Research (BMBF), which has financed the project "Gekonnt

hanDeln" under the grant 13FH007SB7. In addition, we would like to thank all project collaborators as well as all participants of our

# REFERENCES

[1] Claus Atzenbeck, Sam Brooker, and Daniel Rossner. 2023. Storytelling Machines.

In Proceedings of the 6th Workshop on Human Factors in Hypertext (Rome, Italy) (HUMAN '23). Association for Computing Machinery, New York, NY, USA, Article

4, 9 pages. https://doi.org/10.1145/3603607.3613481

[2] Harrison Chase. 2022. LangChain. https://github.com/langchain-ai/langchain.

[3] Douglas Engelbart. 1962. Augmenting human intellect: A conceptual framework.

Summary report. Stanford Research Institute, on Contract AF 49, 638 (1962), 1024.

[4] Alejandro Fernandez, Torsten Holmer, Jessica Rubart, and Till Schuemmer. 2002.

Three Groupware Patterns from the Activity Awareness Family.. In EuroPLoP.

Citeseer, UVK Universitatsverlag Konstanz GmbH, Konstanz, Germany, 375-394.

[5] Daniel Merlin Goodbrey. 2017. The impact of digital mediation and hybridisation

on the form of comics. Ph. D. Dissertation. University of Hertfordshire, School of

[6] Valentin Grimm, Laura Geiger, Jessica Rubart, and Gudrun Faller. 2022. Require-

ments and Design of a Training System for Domestic Workers. In 20. Fachtagung

Bildungstechnologien (DELFI). Gesellschaft fur Informatik e.V., Bonn, 213-214.

https://doi.org/10.18420/delfi2022-037

[7] Miguel Grinberg. 2018. Flask web development: developing web applications

[8] Frode Hegland. 2023. IA, not only AI. In Proceedings of the 34th ACM Conference

on Hypertext and Social Media (Rome, Italy) (HT '23). Association for Computing

Machinery, New York, NY, USA, Article 2, 5 pages.

https://doi.org/10.1145/

[9] Jack Kelly, Alex Calderwood, Noah Wardrip-Fruin, and Michael Mateas. 2023.

There and Back Again: Extracting Formal Domains for Controllable Neurosymbolic Story Authoring. Proceedings of the AAAI Conference on Artificial Intel-

ligence and Interactive Digital Entertainment 19, 1 (Oct. 2023), 64-74.

//doi.org/10.1609/aiide.v19i1.27502

[10] Michael Mateas and Andrew Stern. 2002. Towards integrating plot and character

for interactive drama. In Socially intelligent agents: Creating relationships with

computers and robots. Springer, Heidelberg, 221-228.

[11] Nick Montfort. 2013.

# Riddle Machines: The History and Nature of Interac-

John Wiley & Sons, Ltd, Boschstrasse 12, 69469 Weinheim,

Germany, Chapter 14, 267-282.

https://doi.org/10.1002/9781405177504.ch14

arXiv:https://onlinelibrary.wiley.com/doi/pdf/10.1002/9781405177504.ch14

[12] Theodor Holm Nelson. 1999. Xanalogical structure, needed now more than ever:

parallel documents, deep links to content, deep versioning, and deep re-use. ACM

# Comput. Surv. 31, 4es (dec 1999), 33-es. https://doi.org/10.1145/345966.346033

[13] Eric Nichols, Leo Gao, and Randy Gomez. 2020. Collaborative Storytelling with

Large-scale Neural Language Models. In Proceedings of the 13th ACM SIGGRAPH Conference on Motion, Interaction and Games (Virtual Event, SC, USA) (MIG '20). Association for Computing Machinery, New York, NY, USA, Article 17, 10 pages.

https://doi.org/10.1145/3424636.3426903

[14] Dimitra Petousi, Akrivi Katifori, Katerina Servi, Maria Roussou, and Yannis

Ioannidis. 2022. History education done different: A collaborative interactive digital storytelling approach for remote learners. In Frontiers in Education, Vol. 7.

Frontiers Media SA, Avenue du Tribunal-Federal 34, 1005 Lausanne, Switzerland,

942834. https://doi.org/10.3389/feduc.2022.942834

[15] Giorgio Busi Rizzi. 2023. All click and no play: how interactive are interactive

digital comics?. In Proceedings of the 34th ACM Conference on Hypertext and Social Media (Rome, Italy) (HT '23). Association for Computing Machinery, New York,

# NY, USA, Article 17, 7 pages. https://doi.org/10.1145/3603163.3609052

[16] Jessica Rubart. 2007. Architecting structure-aware applications. In Proceedings

of the Eighteenth Conference on Hypertext and Hypermedia (Manchester, UK) (HT '07). Association for Computing Machinery, New York, NY, USA, 185-188.

https://doi.org/10.1145/1286240.1286296

[17] Jessica Rubart and Nick Montfort. 2003. ifMap: A Mapping System for Coopera-

tively Playing Interactive Fiction Online. In Proceedings of the Technologies for

# Interactive Digital Storytelling and Entertainment (TIDSE) Conference'03. Fraun-

hofer IRB Verlag, Darmstadt, 364-369.

[18] Ben Shneiderman. 2020.

Human-Centered Artificial Intelligence: Reliable,

Safe & Trustworthy.

# International Journal of Human-Computer Interac-

tion 36, 6 (2020), 495-504.

https://doi.org/10.1080/10447318.2020.1741118

arXiv:https://doi.org/10.1080/10447318.2020.1741118

[19] DL Smith, MH Hamrick, and DJ Anspaugh. 1981. Decision story strategy: a

practical approach for teaching decision making. The Journal of school health 51,

10 (December 1981), 637--640. https://doi.org/10.1111/j.1746-1561.1981.tb02110.x

[20] Jing Wu and Der-Thanq Victor Chen. 2020. A systematic review of educational

digital storytelling. Computers & Education 147 (2020), 103786. https://doi.org/

10.1016/j.compedu.2019.103786

[21] Zhuohan Xie, Trevor Cohn, and Jey Han Lau. 2023. The Next Chapter: A Study

of Large Language Models in Storytelling. https://doi.org/10.48550/arXiv.2301.

09790 arXiv:2301.09790 [cs.CL]

[22] Qing Ru Yong and Alex Mitchell. 2023. From Playing the Story to Gaming the

System: Repeat Experiences of a Large Language Model-Based Interactive Story.

In Interactive Storytelling, Lissa Holloway-Attaway and John T. Murray (Eds.).

Springer Nature Switzerland, Cham, 395-409.

[23] Ann Yuan, Andy Coenen, Emily Reif, and Daphne Ippolito. 2022. Wordcraft:

story writing with large language models. In 27th International Conference on

Intelligent User Interfaces. Association for Computing Machinery, New York, NY,

[24] Penghao Zhao, Hailin Zhang, Qinhan Yu, Zhengren Wang, Yunteng Geng,

Fangcheng Fu, Ling Yang, Wentao Zhang, Jie Jiang, and Bin Cui. 2024.

Retrieval-Augmented Generation for AI-Generated Content: A Survey.

arXiv:2402.19473 [cs.CV] https://arxiv.org/abs/2402.19473

[25] Zoie Zhao, Sophie Song, Bridget Duah, Jamie Macbeth, Scott Carter, Monica P Van,

Nayeli Suseth Bravo, Matthew Klenk, Kate Sick, and Alexandre L. S. Filipowicz.

2023. More human than human: LLM-generated narratives outperform humanLLM interleaved narratives. In Proceedings of the 15th Conference on Creativity and

Cognition (Virtual Event, USA) (C&C '23). Association for Computing Machinery,

# New York, NY, USA, 368-370. https://doi.org/10.1145/3591196.3596612

# APPENDIX

# RESEARCH METHODS

Original German Survey

- Q1.1: War die Anwendung insgesamt leicht zu verstehen?

- Q1.2: War die Anwendung insgesamt leicht zu bedienen?

- Q1.3: Hattest du einen guten Uberblick uber deine Geschichte,

als sie langer geworden ist?

- Q1.4: Fiel es dir leicht, Charaktere, Sprechblasen und Antwort-

moglichkeiten anzupassen (Position, Grosse, ...)

* Perceived GPT performance:

- Q2.1: Waren die Text-, Ortund Charaktervorschlage von

# ChatGPT relevant fur deine Geschichte?

- Q2.2: Haben dich die "Gedanken" von ChatGPT bei der

# Erstellung der Geschichte unterstutzt?

- Q2.3: Wurden die Informationen, die du ChatGPT mit-

gegeben hast, sinnvoll in die Empfehlungen einbezogen?

- Q2.4: Konntest du ChatGPT uber die angebotenen Felder,

alle Informationen mitgeben, die relevant fur die Geschichte

- Q2.5: Waren die Kontext-Vorschlage von ChatGPT hilfre-

ich fur deine Geschichte?

- Q2.6: Hat es dich motiviert, die Geschichte weiterzuschreiben,

um zu sehen welche Vorschlage ChatGPT als nachstes

* Comparison of GPT and non-GPT assisted application:

- Q3.1: Mach eine Abschatzung: Wie sehr haben die Empfehlun-

gen von ChatGPT die Entwicklung der Comics beschleu-

- Q3.2: Mach eine Abschatzung: Wie sehr haben die Empfehlun-

gen von ChatGPT die Qualitat der Comics erhoht?

* General remark:

- Nimm dir etwas Zeit und schreib auf, welche Moglichkeiten

dir in der Anwendung gefehlt haben. Im speziellen, welche

weiteren Interaktionsmoglichkeiten hattest du dir mit dem

# Empfehlungssystem gewunscht?

Original German Prompts

tions to produce an outline recommendation

Outline Recommendation Prompt

Ich schreibe interaktive Geschichten mit einem von mir selbst entwick-

elten Editor. Der Editor ist dafur gedacht, Geschichten zu erstellen

in denen zwei Personen interagieren. Der Kontext der Geschichten

sind privat angestellte Hausangestellte Hausangestellte wie Reini-

gungskrafte oder Gartner. Die Angestellten interagieren aufgrund von

unvorhersehbaren oder vorhersehbaren Ereignissen mit dem Arbeitgeber und geraten in eine Situation, in der sie eine schwierige Entscheidung uber ihr weiteres Vorgehen treffen mussen. Kannst du fur mich

ein paar kreative Story-Skizzen fur solche interaktiven Geschichten in deutscher Sprache erstellen? - Das Szenario spielt im Kontext der fol-

genden Tatigkeit: {workArea} - Der/die Arbeitgeber*in heisst: employer.

Uber diese Person ist folgendes bekannt: {employerInfo} - Der/die Hau-

sangestellte heisst: {employee}. Uber diese Person ist folgendes bekannt:

{employeeInfo} Bitte erzeuge einen kreativen Geschichtskontext fur

eine solche interaktive Geschichte. The output should be a markdown

code snippet formatted in the following schema, including the leading and trailing ""'json" and ""'": "'json { "Kontext": string // Ein Vorschlag

fur den Kontext der Geschichte. 30 - 50 Worter. "Entscheidungspunkt":

string //Erklarung des Entscheidungspunkts der Geschichte. Circa 30

tions to produce a frame recommendation

Frame Recommendation Prompt

Du schreibst eine interaktive Geschichte, in der ein Szenario von

privat angestellten Hausangestellten mit folgenden Eigenschaften

beschrieben wird: - Maximal zwei Charaktere interagieren miteinander

- Das Szenario spielt im Kontext der folgenden Tatigkeit: {workArea}

- Der/die Arbeitgeber*in heisst: {employer}. Uber diese Person ist fol-

gendes bekannt: employerInfo - Der/die Hausangestellte heisst: {em-

ployee}. Uber diese Person ist folgendes bekannt: {employeeInfo} - Die

Geschichte ist in folgenden Kontext eingebettet: {outline} - Die gle-

iche Person kann mehrere Textabschnitte hintereinander sagen - Die

Geschichte dient zur Weiterbildung der Hausangestellten - Es soll eine

runde Geschichte entstehen, die eingeleitet wird und hin zu einem

# Entscheidungsszenario (Auswahl zwischen drei Moglichkeiten) fur

die Hausangestellte Person fuhrt - Nach der Entscheidung wird die

Geschichte in den Schlussteil gefuhrt Gib einen einzelnen Textabschnitt an, sowie den Namen des Charakters und den Ort, an dem sich dieser befindet, um die Geschichte zu beginnen. The output should be a

markdown code snippet formatted in the following schema, including

the leading and trailing ""'json" and ""'": "'json { "Charaktername": string // Der Vorname des Charakters. "Rolle": string // Die Rolle des

Charakters in der Geschichte. "Text": string // Der Textabschnitt, der vom Charakter gesagt wird. Maximal ein Satz und 50 Zeichen. "Ort": string // Der Ort, an dem sich der Charakter befindet. } "' Die bisherige

# Geschichte lasst sich folgendermassen zusammenfassen: {summary}

Die letzten zwei Aussagen sind: {last_messages} Der Textabschnitt wird

von {character_choice} gesprochen.

