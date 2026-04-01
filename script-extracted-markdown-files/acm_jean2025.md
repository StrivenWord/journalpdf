---
title: "Easing the Block-to-Text Transition: A Scaﬀolded Approach to Learning Python"
subtitle: "Python DEVIN JEAN , Vanderbilt University, Nashville, TN, United States GORDON STEIN , Vanderbilt University, Nashville, TN, United States BRIAN BROLL"
doi: "10.1145/3736181.3747126"
---


Latest updates: hps://dl.acm.org/doi/10.1145/3736181.3747126

RESEARCH-ARTICLE Easing the Block-to-Text Transition: A Scaffolded Approach to Learning

DEVIN JEAN, Vanderbilt University, Nashville, TN, United States GORDON STEIN, Vanderbilt University, Nashville, TN, United States BRIAN BROLL, Vanderbilt University, Nashville, TN, United States AKOS LEDECZI, Vanderbilt University, Nashville, TN, United States

Open Access Support provided by: Vanderbilt University

3736181.3747126.pdf

Total Downloads: 234

Published: 21 October 2025 Citation in BibTeX format CompEd 2025: ACM Global Computing Education Conference 2025 October 21 - 25, 2025 Gaborone, Botswana Conference Sponsors:

Easing the Block-to-Text Transition: A Scaffolded Approach to

Learning Python

Devin Jean

Gordon Stein

Vanderbilt University

Vanderbilt University

Nashville, Tennessee, USA

Nashville, Tennessee, USA

devin.c.jean@vanderbilt.edu

gordon.stein@vanderbilt.edu

This paper introduces PyBlox, a novel hybrid programming environment designed to facilitate the transition from block-based programming to text-based programming in Python. The transition from visual to textual programming represents a significant pedagogical challenge that PyBlox addresses by preserving key programming features that make block-based environments engaging while introducing students to Python's syntax. PyBlox implements a hybrid transitional approach with a text-based editor augmented by a palette of graphical blocks. It maintains continuity across environments by faithfully implementing the concurrency model, graphics capabilities, and networking features of modern block-based environments. A classroom study with 25 high school students revealed that PyBlox effectively supports feature discovery through its drag-and-drop block palette, text completion suggestions, and documentation panel. Analysis of project construction logs showed that 63% of block insertions involved first-time feature discovery, with students gradually shifting toward manual text editing as they gained Python proficiency. This study demonstrates PyBlox's effectiveness in providing a gentle slope between blockbased and text-based programming, expanding the accessibility of text-based programming while maintaining student engagement.

CCS Concepts * Software and its engineering - Integrated and visual development environments; Software usability; * Social and professional topics - Computer science education; * Humancentered computing - Graphical user interfaces; User stud-

Keywords computer science education, block-based programming, python, programming environments, mediated transfer



This work is licensed under a Creative Commons Attribution 4.0 International License. CompEd 2025, Gaborone, Botswana (c) 2025 Copyright held by the owner/author(s). ACM ISBN 979-8-4007-1929-5/2025/10 https://doi.org/10.1145/3736181.3747126

Brian Broll

Akos Ledeczi

Vanderbilt University

Vanderbilt University

Nashville, Tennessee, USA

Nashville, Tennessee, USA

brian.broll@vanderbilt.edu

akos.ledeczi@vanderbilt.edu

Introduction

The transition from block-based to text-based programming represents a significant pedagogical challenge in computer science education. While block-based environments like Scratch [ 11], Snap ! [ 15], and NetsBlox [ 3] offer intuitive entry points for novice programmers through visual interfaces and simplified programming constructs, professional programming practice still demands proficiency with text-based languages. This creates a critical gap that students must navigate, often with limited support. Current research [ 12] suggests that this transition can introduce substantial cognitive load as students simultaneously grapple with syntax rules, programming concepts, and new development environments, together forming the "modality shift" learning barrier. To address this challenge, we introduce PyBlox, a novel hybrid programming environment designed to facilitate the transition from block-based programming in NetsBlox/ Snap ! to text-based programming in Python. PyBlox maintains substantial similarity with the source environment while providing scaffolding to help students develop proficiency with the target language. Unlike many transitional tools that focus narrowly on syntax conversion, PyBlox preserves key programming features that make block-based environments engaging and accessible--including graphics capabilities, concurrency models, and networking features--while introducing students to Python's syntax and programming paradigms. PyBlox is especially suitable for novice users of NetsBlox, a blockbased programming environment specifically designed to introduce advanced computing concepts like networking, distributed computing, the Internet of Things (IoT), cybersecurity, and artificial intelligence (AI) in K12 [ 3]. Two distributed computing abstractions-- Remote Procedure Calls (RPCs) and message passing--and only three new blocks are needed to enable students to engage with online data sources and services, such as Google Maps, the Movie Database, various AI resources, and many others, and create social applications like multi-player games or a chat room. These same abstractions and blocks can also be used to remotely access smartphone sensors [ 8], remotely control real robots or virtual ones in shared simulated 3D worlds [ 16], or even create a digital band that plays music synchronized across multiple computers [ 5]. PyBlox maintains support for all of these advanced computing features throughout the transition from NetsBlox to Python. This paper presents the design principles underlying PyBlox, details its implementation, and examines preliminary findings from a classroom study. We evaluate how PyBlox's feature set supports students in transferring their existing programming knowledge and building authentic Python projects. Special attention is given to PyBlox's innovative approaches to concurrency, graphical support, and networking abstractions, which allow students to create

Python programs with similar capabilities to NetsBlox. By providing a gentle learning curve between block-based and text-based programming, PyBlox aims to expand the accessibility of text-based programming to a broader range of students while maintaining the engagement and creativity fostered by block-based environments. The included study aimed to address three primary research questions: (1) whether students find it easy to create similar, NetsBloxlike effects in Python using PyBlox; (2) if PyBlox's discoverability features (i.e., the blocks palette, method suggestions, and the documentation panel) are sufficient for feature discovery; and (3) how students rank the authenticity of PyBlox compared to block-based and professional programming.

Theoretical Foundations

The pedagogical challenge of transitioning students from blockbased to text-based programming involves what researchers call "mediated transfer," which includes two primary techniques: bridging and hugging [ 4]. Bridging techniques actively help students transfer knowledge from one domain to another through explicit instruction on analogous concepts, such as teaching data types by analogy to real-world concepts like questions (booleans) or explaining loops through familiar repetitive tasks like daily chores. These techniques typically do not require modifying either programming environment; instead, they focus on conceptual connections. Hugging techniques, by contrast, involve making changes to at least one of the domain areas to reduce the number or significance of differences between them. The theoretical rationale behind hugging suggests that reducing surface-level differences allows students to focus more directly on conceptual transfers rather than getting distracted by superficial variations. The literature identifies several distinct paradigms for implementing these transitions: one-way transition environments, which allow irreversible conversion from blocks to text; dual-modality environments, which enable bidirectional conversion between representations; and hybrid environments, which combine elements from both worlds in an integrated experience [ 10]. Each approach embodies different theoretical assumptions about how knowledge transfers occur between programming modalities and the barriers students face in this transition. The "syntax barrier" represents a particular theoretical concern, wherein novices must simultaneously manage cognitive load from syntax rules, programming concepts, and new development environments. While some studies on these transitional systems show statistically significant improvements in student performance with transitional tools, others reveal more nuanced patterns. For instance, studies of Pencil Code demonstrated that students initially used the block editor over 75% of the time, but gradually transitioned to using the text editor over 90% of the time [ 2]. Analysis of when students choose to transition between views provides insight into the specific cognitive challenges they face--for example, moving to the block editor for command discovery or to manipulate program structure and scope. These empirical findings inform the theoretical understanding of how students navigate the block-to-text transition, revealing both the value of continued scaffolding and the importance of gradual independence.

PyBlox positions itself uniquely within this theoretical landscape by employing a comprehensive approach that combines both bridging and hugging techniques. As a hybrid environment, PyBlox implements hugging through its preservation of NetsBlox's feature set and familiar IDE layout, while simultaneously providing bridging through its explicit Python equivalents for block constructs. Unlike one-way transition environments that require an abrupt leap to text, or dual-modality environments that may permit students to avoid text entirely, PyBlox requires students to engage directly with Python syntax while still providing scaffolding.

The classroom study results align with theoretical expectations: the high percentage of unique block insertions (62.9%) confirms the value of this approach for promoting feature discovery, while the increasing ratio of manual edits to block insertions demonstrates the gradual removal of scaffolding as expertise develops. Moreover, PyBlox's emphasis on preserving advanced concepts like concurrency and networking addresses a gap in transitional tool theory, which has typically focused on basic programming constructs rather than complex but high-level computational concepts. This suggests that PyBlox may be particularly valuable in contexts where students have already mastered sophisticated programming concepts in block-based environments and need to transfer that advanced knowledge to text-based environments.

Related Work

As for existing technologies, Alice 3 pioneered the one-way transition approach, allowing students to create block-based programs with "Java-like" syntax and then export them to NetBeans as fullyfunctional Java code [ 4]. Other similar platforms include Blockly, Google's web-based block programming environment which supports code generation in multiple languages like JavaScript and Python [ 6], and EduBlocks, which similar to Blockly supports oneway environments for a variety of languages including JavaScript and Python [ 7]. While conceptually similar to PyBlox, these environments do not incorporate advanced features like networking, concurrency, or project conversion that make PyBlox particularly suitable for students already familiar with NetsBlox's advanced capabilities. Additionally, unlike PyBlox, Alice 3 provides no graphical block support after exporting, requiring students to make a complete leap to text-based programming once they transition. To mitigate this, a new environment known as Pencil Code established the dual-modality paradigm, offering a block view and text view of the same program that students can switch between at will [ 18]. The editor animates the transition between blocks and text, helping students visualize the connection. Droplet, the general purpose bidirectional block-to-text engine underlying Pencil Code, has also been used in other transitional projects, such as Code.org's App Lab targeting JavaScript [ 1]. While Pencil Code and (in general) Droplet allow bidirectional conversion, PyBlox instead integrates blocks directly into a text editor environment, requiring students to work primarily with text while using blocks as assistive discovery elements. Unlike PyBlox, Pencil Code and Droplet also do not attempt to bridge from contemporary block-based environments, but rather require students to learn a separate, dedicated block-based language before being able to make the transition to text.

As an alternative to the one-way and bidirectional conversion approaches, other hybrid approaches were later developed. One such hybrid environment was Stride (integrated into the Greenfoot Java IDE), which introduced frame-based editing where larger programming constructs are scaffolded with frames while students write individual statements in text [ 14]. Another highly similar platform is Strype, a Stride-style frame-based editor for Python [ 9]. This frame-based hybrid approach differs from PyBlox's drag-anddrop assistance model, as Stride and Strype completely restructure how code is edited rather than augmenting a standard text editor. As yet another alternative approach, a later development was the Pencil.cc environment, which extended Pencil Code's concepts by offering a hybrid mode where a purely textual editor is supplemented with a palette of block snippets [ 19]. While similar to PyBlox in basic approach, Pencil.cc lacks PyBlox's focus on preserving the concurrency model and networking capabilities of its source environment. However, this was later addressed by a new browser-based platform known as Pytch, a Scratch to Python transitional environment that provides a Python text editor augmented with a palette of Scratch blocks and their Python equivalents.

Pytch represents the tool most similar to PyBlox, being specifically designed to transition from Scratch to Python with a palette of Scratch-equivalent blocks that can be copied and pasted into a text editor [ 17]. Although Pytch and PyBlox were designed in parallel, they both have several notable similarities, including the use of decorators for defining events/scripts and the recreation of the Scratch/NetsBlox concurrency model in a Python environment. However, while Pytch implements the Scratch-like concurrency model through a modified Python interpreter, PyBlox achieves similar functionality using standard Python threading with automatic yield points, allowing learned skills to transfer better to standard Python environments.

PyBlox Design

The fundamental design philosophy of PyBlox centers on maintaining continuity in both programming language features and the development environment across the transition from block-based to text-based programming. Thus, rather than forcing students to make a sudden leap to pure Python programming, PyBlox offers a graduated approach that allows students to leverage their existing knowledge of NetsBlox/Snap ! while learning Python. PyBlox implements a hybrid transitional approach, providing a text-based editor augmented with a palette of graphical blocks that can be dragged and dropped to insert equivalent Python code. This IDE is presented in Figure 1. The block palette in PyBlox currently contains 137 blocks from NetsBlox, organized into the same color-coded categories, providing a familiar interface for students exploring Python equivalents of familiar operations. PyBlox includes a comprehensive graphics and sprite system that extends beyond basic turtle graphics to replicate the full feature set of NetsBlox/ Snap !. Students can create sprites with custom costumes, scaling, collision detection, and so on. Many of these graphical features are exposed as Python properties (e.g., self. pen_color = 'blue', self. visible = False, or self. heading = 60), which avoids an overreliance on get/set methods and gives students additional practice with Python variables and fields.

A key architectural achievement in PyBlox is its implementation of the NetsBlox/ Snap ! concurrency model in standard Python. Rather than modifying the Python interpreter (as done in other tools such as Pytch [ 17]) and increasing the gap between the transitional environment and pure Python, PyBlox uses native Python threading with decorator-based script definitions. Scripts decorated with, e.g., @onstart () or @onkey (keys. up) automatically spawn new threads which are managed by a custom event scheduler. Students' code is also preprocessed to add yield points at appropriate locations, (roughly) ensuring fair execution between threads, similar to the behavior in block-based environments. A unique aspect of PyBlox compared to other platforms is its comprehensive support for novice-friendly networking features, which are exposed by a global NetsBlox client instance, nb. Students can use this client to access all NetsBlox features, including Remote Procedure Calls (RPCs) and message passing between projects. NetsBlox RPCs can be accessed directly through the nb object; for example, nb. cloud_variables. get_variable('test') accesses the GetVariable RPC of the NetsBlox CloudVariables service. For convenience, PyBlox automatically converts between Python and NetsBlox types as necessary; e.g., converting NetsBlox "structured data" into a Python dictionary. See Figure 2 for an example of equivalent NetsBlox and PyBlox programs which make use of RPCs to display a live weather radar animation. To send messages over the internet, PyBlox provides nb. send_message(), and a special @nb. on_message() decorator can be used to receive messages. Notably, PyBlox clients can communicate not only with other PyBlox clients but also with standard browser-based NetsBlox clients, enabling mixed-language collaborative projects. The PyBlox IDE maintains a layout reminiscent of NetsBlox/ Snap !

while providing modern text editor features. The editor is divided into tabs for global, stage, and sprite-specific code, preserving the organizational structure students are familiar with from block-based environments and helping students manage complexity by hiding unrelated code from other entities. Variables from each tab can be accessed through, e.g., globals. var, stage. var, or sprite. var, creating a consistent, clear pattern of access regardless of where the variable is defined. The IDE also includes multiple features to assist students in writing Python code, such as: context-aware completion suggestions, an always-visible documentation panel that updates based on the current selection, syntax highlighting, and automatic indentation. A dedicated "Program Output" panel displays the stdout and stderr streams from the running program, and a special "watcher" system allows students to monitor the values of variables in real-time, similar to NetsBlox/ Snap !. Additionally, PyBlox provides extensibility through its customizable block palette. Teachers can add blocks specific to particular lessons, such as blocks for numpy or opencv operations, with custom documentation and insertion behavior. This allows the tool to grow with students' expanding Python knowledge.

A powerful feature of PyBlox is its ability to automatically con-

vert existing NetsBlox projects into Python. Rather than requiring students to manually recreate their block-based programs in Python, they can import an existing NetsBlox project and continue development in Python. This conversion uses a sophisticated system of wrapped Python types that overload operators to maintain NetsBlox-like semantics while still producing simple, readable

PyBlox happens in a separate process and popup window unlike in typical block-based environments.

Python code. PyBlox also supports exporting projects as standalone Python scripts that can be run independently of PyBlox. This creates a complete pathway from NetsBlox, to PyBlox, and finally to standard Python. By combining the familiarity of NetsBlox's feature set with the unrestricted power of Python, PyBlox creates a bridge that allows students to carry forward both their conceptual knowledge and practical projects into the world of text-based programming. This comprehensive approach--preserving graphics capabilities, concurrency, networking, and the overall programming environment structure--distinguishes PyBlox from other transitional tools that focus on a more limited subset of features or require students to leave their familiar environment entirely.

To evaluate PyBlox, a classroom study was conducted with 25 high school students from the School for Science and Math at Vanderbilt (SSMV) during 2024. This study was structured in two phases: an initial phase of four daily 3-hour sessions in June where students learned basic programming concepts through the construction of game-based projects in NetsBlox, followed by a second phase of six 2-hour weekly sessions in October/November where students transitioned to PyBlox, creating similar game-based projects. To address our research questions, students were asked to complete pre-, mid-, and post-surveys containing twenty 5-point Likertscale questions assessing general CS sentiments. These surveys were administered at the beginning of the first phase, at the end of the first phase, and at the end of the second phase, respectively. After completing the post-survey, students were asked an additional eight 5-point Likert-scale questions related to their experiences using PyBlox and Python. Next, students completed a short 6-question test, which asked them to interpret and compose short Python programs related to turtle graphics, iteration, and list manipulation.

Finally, the study concluded with voluntary individual student interviews to gather more detailed responses and feedback. In addition to the surveys, post-test, and interviews, we also collected thorough logging data from every student's use of the PyBlox program editor over the entire duration of the second phase of the study. This logging data includes every IDE interaction, including tab changes, block drag-and-drop operations, text insertions, and so on.

In total, 25, 22, and 21 students completed the pre-, mid-, and postsurveys, respectively. The 20 CS sentiment survey questions were grouped into five categories and were verified to be internally consistent by both the Cronbach's and the McDonald's metrics [ 13]. Seven students (4 female and 3 male) volunteered for closing interviews. Of these seven, only one had any significant Python programming experience prior to the study. Another three had block-based programming experience, but no text-based experience. Two had no prior programming experience.

The surveys revealed that students rated PyBlox discoverability features highly, with the drag-and-drop block palette (4.0/5), text completion suggestions (4.1/5), and documentation panel (3.8/5) each receiving positive evaluations. In closing interviews, all seven interviewees reported successfully using the drag-and-drop system when unsure how to access certain features in Python. One student noted, "I dragged in blocks when I was confused about how to achieve some effect or to see how they get translated into text." Additionally, all interviewed students claimed that learning NetsBlox before PyBlox was personally useful for learning Python, typically mentioning that it provided something to "bridge off of" rather than starting "completely from scratch." When asked if they noticed any missing features from NetsBlox when using PyBlox (with an emphasis on code-writing and debugging features), six of seven students responded "no," with the one remaining student mentioning only a specific dropdown menu issue that was subsequently

code in PyBlox. Omitted from both is a small separate script on the stage which sets the background to a Google Maps image.

resolved. This suggests that PyBlox successfully recreated the essential programming capabilities of NetsBlox within a Python context. When asked about the perceived differences between PyBlox and standard Python, five of seven interviewed students stated they were "effectively the same" but that PyBlox was easier to learn and served as a helpful guide when getting started. One student with previous Python experience found PyBlox confusing because it included features that were not "fully Python" (Ironically, these were standard Python features like classes and decorators that the student had simply not encountered before). Thus, we observe that 5/6 novice students perceived PyBlox to be an authentic Python programming experience. Post-survey results showed students rated their interest in continuing with Python slightly higher (3.1/5) than with PyBlox (2.8/5). Two of the students who expressed interest in continuing with PyBlox also stated they would like to learn standard Python, and both felt PyBlox had prepared them for that transition. These findings suggest that PyBlox successfully positioned itself as a stepping stone toward "real" Python programming. When asked if they would recommend PyBlox to a friend interested in learning Python, five students responded positively, one said "probably," and only one (who already knew Python) equivocated, suggesting they might recommend an online Python course instead. Analysis of project construction logs revealed that 62.9% of block insertions were "unique" or first-time uses, suggesting the block palette effectively supported feature discovery. This serves as both a reproduction of a previous result from Weintrop and Holbert [ 18] and, due to using a text-only program editor, a confirmation of one of their concluding hypotheses. Additionally, we observed that the ratio of manual text edits to block insertions increased throughout the study (from 4.5 to 21.6), indicating that students gradually relied less on blocks as they began to learn Python syntax. This agrees with interview responses, in which six of seven students claimed their use of the drag-and-drop system decreased over time as they memorized the syntax for frequently used features. The post-test revealed varying levels of Python comprehension. Students performed best on questions related to graphics and visualizations (55% correct responses for spiral drawing questions), aligning with the project-based nature of the curriculum. They

struggled more with questions involving list operations and variables (24% correct responses), highlighting areas for improvement in instruction. A common error pattern suggested that some students had difficulty with code block scope and indentation, with at least seven students showing persistent indentation errors in their written code submissions. Another recurring issue was confusion between variable identifiers and string literals containing the variable name - for example, using "name" (the string) instead of name (the variable identifier). Six incorrect responses on one question stemmed from this exact confusion.

countered as students constructed and executed programs during the second phase of the study. From this, we find that around 57.3% of runtime exceptions were caused by variable issues (either undefined or misspelled symbols). This is similar to the variable issues identified in the post-test; however, we did not observe the confusion between strings and identifiers as a predominant source of errors here. This is likely due to the presence of syntax highlighting for strings in PyBlox, whereas a plain text editor was used for the post-test to prevent students from employing guess-and-check techniques or receiving syntactic assistance from the IDE.

Analysis of project logs revealed the top three block categories as "control" (38.7%), "motion" (25.4%), and the combined "art" categories. This aligns with previous research on block-based environments [ 18], though PyBlox showed a higher percentage of control blocks, likely due to the more logically complex game-based

projects used in the curriculum. The study also examined whether PyBlox affected students' attitudes toward computer science. Survey results showed no statistically significant changes in students' computer science sentiment across pre-, mid-, and post-surveys. However, in interviews, three students reported increased interest in computer science, three reported no change, and one response was inconclusive.

The data from our evaluation show strong evidence that PyBlox successfully provides scaffolding for feature discovery while gradually transitioning students to manual text editing. This finding is consistent with similar studies on other hybrid environments. However, our study enriches the understanding of the block-to-text transition in several important ways. First, unlike many prior studies that focus primarily on basic programming constructs, PyBlox maintains support for advanced features including concurrency, networking, and sprite-based interactions--features central to student engagement but often abandoned in transitional tools. Second, our logging data reveal the specific timeline and pattern of transition from block-reliance to text-based coding, demonstrating that most students organically reduce their dependence on blocks without explicit instruction to do so. The increasing ratio of manual edits to block insertions (reaching 21.6 by the end of the study) indicates a successful gradual removal of scaffolding as expertise develops. A particularly valuable insight emerged from our error analysis of student code. While most transitional tools address the "syntax barrier" as a uniform challenge, our data reveals a more nuanced picture where specific aspects of Python syntax (particularly variable scope and indentation) present persistent difficulties even as students become comfortable with other syntactic elements. This suggests that targeted scaffolding addressing these specific pain points--perhaps through special-purpose blocks or enhanced visual indentation guides--could further smooth the transition. Additionally, the confusion between strings and identifiers points to a conceptual barrier that transcends pure syntax challenges and relates to fundamental programming concepts. Future developments of PyBlox could incorporate more explicit instruction and visual cues to help students better distinguish between these elements. Overall, PyBlox appears to effectively serve as a bridge between block-based and text-based programming. Students found its supporting features useful, and the majority perceived it as providing an authentic Python programming experience despite its transitional nature. The drag-and-drop block palette proved particularly valuable for feature discovery, with usage patterns suggesting students appropriately decreased their reliance on it as they gained Python proficiency. Future improvements could include support for defining and accessing variables from the block palette, as well as the inclusion of more explicit instruction on critical syntactic elements such as code block scope and indentation. Additionally, the study identified a need for clearer demonstrations of how to make effective use of components such as the documentation panel, as some students were initially unsure how to use this feature in practice to assist in program construction. Despite the limited duration of the study (effectively only 7 hours and 40 minutes of actual Python instruction due to technical issues and testing requirements), students demonstrated reasonable progress in learning Python through PyBlox. The tool's perceived

authenticity and the students' gradual shift from block-based to text-based code additions indicate that PyBlox successfully achieved its goal as a transitional platform between NetsBlox and Python and provide promising early evidence for its broader applicability in introductory programming education. Concerning the study participants, it should be noted that SSMV is a selective program that only admits students with an interest in STEM topics, which serves as a possible source of bias for these results. However, in the pre-survey, students rated their level of previous Python programming experience quite low, with an average of 1.8/5 and a median of 1/5 (the minimum). Additionally, in interview responses, we found that only one of the seven students had a significant level of incoming Python knowledge. We also observed an even split between students who were interested in computer science (2/7) and those who explicitly claimed to have no interest (2/7).

Conclusions

This paper has presented PyBlox, a novel hybrid programming environment designed to ease the transition from block-based to text-based programming. By preserving the key features that make block-based environments engaging while introducing students to Python syntax, PyBlox creates a gentler learning curve than traditional approaches to this critical transition. PyBlox distinguishes itself from other transitional tools through its comprehensive approach: preserving NetsBlox's concurrency model and networking capabilities, supporting automatic project conversion, offering a customizable block palette, and enabling students to export projects as standalone Python programs for continued learning beyond PyBlox. By providing a gentle slope between block-based and text-based programming, PyBlox expands the accessibility of text-based programming to a broader range of students while maintaining the creativity and engagement fostered by block-based environments. The results from our classroom study with 25 high school students demonstrate PyBlox's effectiveness as a transitional tool. We observed that PyBlox's discoverability features were effective for Python novices (RQ 2), as indicated by their relatively high scores in survey responses and students' self-reported extensive use of these features in all seven interviews. On top of this, the high frequency of unique block insertions (62.9%) and gradual increase in manual edits relative to block insertions (from 4.47 to 21.59) show that the block palette is not a crutch, but rather a natural scaffold for real Python learning. Further, the success of these features despite both study phases using the same variety of NetsBlox-style graphical game/app-like projects demonstrates that students were able to easily reproduce NetsBlox-like effects in Python using PyBlox (RQ 1). And most significantly, students perceived PyBlox and Python as "effectively the same," indicating that PyBlox successfully presents an authentic Python programming experience despite its transitional and hybrid nature (RQ 3).

Acknowledgments

This material is based upon work supported by the National Science Foundation under Grant No. 1949472.

References [1] David Bau. 2015. Droplet, a blocks-based editor for text code. Journal of Comput-

ing Sciences in Colleges 30, 6 (2015), 138-144.

[2] David Bau, D. Anthony Bau, Mathew Dawson, and C. Sydney Pickens. 2015.

Pencil Code: Block Code for a Text World. In Proceedings of the 14th International Conference on Interaction Design and Children (Boston, Massachusetts) (IDC '15). Association for Computing Machinery, New York, NY, USA, 445-448. doi:10.1145/2771839.2771875

[3] Brian Broll, Akos Ledeczi, Gordon Stein, Devin Jean, Corey Brady, Shuchi Grover,

Veronica Catete, and Tiffany Barnes. 2021. Removing the Walls Around Visual Educational Programming Environments. In 2021 IEEE Symposium on Visual Languages and Human-Centric Computing (VL/HCC). 1-9. doi:10.1109/VL/HCC51201.

[4] Wanda Dann, Dennis Cosgrove, Don Slater, Dave Culyba, and Steve Cooper.

2012. Mediated Transfer: Alice 3 to Java. In Proceedings of the 43rd ACM Technical Symposium on Computer Science Education (Raleigh, North Carolina, USA) (SIGCSE '12). Association for Computing Machinery, New York, NY, USA, 141-146. doi:10.1145/2157136.2157180

[5] T. Ebiwonjumi, W. Hedgecock, D. Jean, G. Barnard, S. Kittani, B. Broll, and A.

Ledeczi. 2024. BEATBLOX: A VISUAL BLOCK-BASED APPROACH TO INTEGRATING MUSIC AND COMPUTER SCIENCE EDUCATION. In EDULEARN24 Proceedings (Palma, Spain) (16th International Conference on Education and New Learning Technologies). IATED, 2431-2440. doi:10.21125/edulearn.2024.0669

[6] Neil Fraser. 2015. Ten things we've learned from Blockly. In 2015 IEEE Blocks and

Beyond Workshop (Blocks and Beyond). 49-50. doi:10.1109/BLOCKS.2015.7369000

[7] Anaconda Inc. 2025. EduBlocks. https://edublocks.org/ Accessed: 2025-03-22. [8] Devin Jean, Brian Broll, Gordon Stein, and Akos Ledeczi. 2021. Your Phone as a

Sensor: Making IoT Accessible for Novice Programmers. In 2021 IEEE Frontiers in Education Conference (FIE). 1-5. doi:10.1109/FIE49875.2021.9637272

[9] Charalampos Kyfonidis, Pierre Weill-Tessier, and Neil Brown. 2021. Strype:

Frame-Based Editing tool for programming the micro:bit through Python. In Proceedings of the 16th Workshop in Primary and Secondary Computing Education (Virtual Event, Germany) (WiPSCE '21). Association for Computing Machinery, New York, NY, USA, Article 6, 2 pages. doi:10.1145/3481312.3481324

[10] Yuhan Lin and David Weintrop. 2021. The landscape of Block-based program-

ming: Characteristics of block-based environments and how they support the transition to text-based programming. Journal of Computer Languages 67 (2021), 101075. doi:10.1016/j.cola.2021.101075

[11] John Maloney, Mitchel Resnick, Natalie Rusk, Brian Silverman, and Evelyn East-

mond. 2010. The Scratch Programming Language and Environment. ACM Trans. Comput. Educ. 10, 4, Article 16 (Nov. 2010), 15 pages. doi:10.1145/1868358.1868363

[12] Luke Moors, Andrew Luxton-Reilly, and Paul Denny. 2018. Transitioning from

Block-Based to Text-Based Programming Languages. In 2018 International Conference on Learning and Teaching in Computing and Engineering (LaTICE). 57-64. doi:10.1109/LaTICE.2018.000-5

[13] Miguel Padilla. 2019. A primer on reliability via coefficient alpha and omega.

Archives of Psychology 3, 8 (2019).

[14] Thomas W. Price, Neil C.C. Brown, Dragan Lipovac, Tiffany Barnes, and Michael

Kolling. 2016. Evaluation of a Frame-based Programming Editor. In Proceedings of the 2016 ACM Conference on International Computing Education Research (Melbourne, VIC, Australia) (ICER '16). Association for Computing Machinery, New York, NY, USA, 33-42. doi:10.1145/2960310.2960319

[15] Bernat Romagosa i Carrasquer. 2019. The Snap! Programming System. Springer

International Publishing, Cham, 1-10. doi:10.1007/978-3-319-60013-0_28-2

[16] Gordon Stein and Akos Ledeczi. 2021. Enabling Collaborative Distance Robotics

Education for Novice Programmers. In 2021 IEEE Symposium on Visual Languages and Human-Centric Computing (VL/HCC). IEEE Computer Society, 1-5.

[17] Glenn Strong and Ben North. 2021. Pytch -- an environment for bridging block

and text programming styles (Work in progress). In Proceedings of the 16th Workshop in Primary and Secondary Computing Education (Virtual Event, Germany) (WiPSCE '21). Association for Computing Machinery, New York, NY, USA, Article 22, 4 pages. doi:10.1145/3481312.3481318

[18] David Weintrop and Nathan Holbert. 2017. From blocks to text and back: Pro-

gramming patterns in a dual-modality environment. In Proceedings of the 2017 ACM SIGCSE technical symposium on computer science education. 633-638.

[19] David Weintrop and Uri Wilensky. 2017. Between a Block and a Typeface: De-

signing and Evaluating Hybrid Programming Environments. In Proceedings of the 2017 Conference on Interaction Design and Children (Stanford, California, USA) (IDC '17). Association for Computing Machinery, New York, NY, USA, 183-192. doi:10.1145/3078072.3079715

