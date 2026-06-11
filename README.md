# "coding" repository

The purpose of this repository is to teach agentic coding to mutiple users. It contains projects organized by user name and project name (e.g., Martin's project Worm would be in the `martin/worm` folder).

Each project is intended to allow the user to explore agent assited coding. For this purpose, the projects will follow the below rules.

## Project Rules

- Each project is in folder `user-name/project-name`.
- Each project should contain a README.md that should reflect all the details of the project, including requirements, design and implementation. Everything that is implemented in code should be reflected in README.md
- Anytime project code is modified, the README.md should be updated as well.
- README.md can contain planned features or changes that have not been implemented, yet. These should be marked with a TODO tag.
- Unless the user specifies otherwise, the project implementation should be done in JavaScipt as single HTML5 file named `index.html`.
- The repository root contains an `index.html` that links to all projects. Whenever a new project is created, add a link to it in the root `index.html`.

## AI Instructions

The project `README.md` files describes each of the projects. It should be kept up to date with all the features of the project. Whenever the user prompts the AI to do updates to the code, this file should be updated as well. Do so by adding the description of the newly implemented feature into the relevant section, or if there is no relevant section, create a new section. The user might mark some features or descriptions in this file as "TODO". That means, the feature is still not implemented in code. If the user asks the AI to implement the feature marked with "TODO", the "TODO" label should be removed and the description of the feature updated if necessary. If the feature was implemented only partially, a description of the parts that were not implemented should be retained with a "TODO" label.

Do not add status updates (like "implemented two player mode") to the README.md, instead describe the current state of the project (e.g., add a section titled "Two Player Mode" with details about th feature).
