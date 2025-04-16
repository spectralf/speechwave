# Cursor Project Initialization Protocol (`cursorproject.md`)

**Objective:** To establish a standardized and effective process for initiating new software projects using Cursor AI, ensuring clarity, alignment, and efficient task management from the outset.

**Instructions for AI:**

Follow this protocol meticulously when a new project is initiated. Your primary goal is to collaborate effectively with the user to define the project and set up the necessary foundational documents.

**Phase 1: Project Clarification & Definition**

1.  **Understand the Goal:** Begin by thoroughly analyzing the user's initial project request.
2.  **Ask Clarifying Questions:** Before proceeding, engage the user in a dialogue to fully understand the project. Ask specific questions about:
    *   The core purpose and goals of the project.
    *   Key features and functionalities required.
    *   Target users or audience.
    *   Preferred technology stack (programming languages, frameworks, libraries, databases, etc.). If unsure, suggest options based on the project type.
    *   Any specific constraints (performance requirements, deadlines, existing codebase integration, etc.).
    *   Desired architectural patterns or coding style preferences.
    *   Any known requirements or external dependencies.
3.  **Summarize Understanding:** Once you believe you have sufficient information, provide a concise summary of your understanding of the project requirements and ask the user for confirmation or correction. Iterate on this step until the user confirms your understanding is accurate.
4.  **Await Initialization Command:** Do not proceed to Phase 2 until the user explicitly gives the command "initialize".

**Phase 2: Project Initialization & Document Generation**

*Trigger: User command "initialize"*

1.  **Research Cursor Best Practices:** Before generating files, perform a quick web search (`@Web`) focusing on "Cursor AI best practices for `.cursorrules`" and "Cursor AI project task list management". This is to ensure the generated rules and task list structure are effective.
2.  **Generate Project Documents:** Based *only* on the confirmed understanding from Phase 1, create the following files in the project root:
    *   **`specification.md`**:
        *   A detailed document outlining the project's confirmed requirements, features, scope, technology stack, and constraints. Use clear headings and structure based on the information gathered.
    *   **`tasklist.md`**:
        *   A detailed, actionable roadmap for the project's development.
        *   Break down the project (as defined in `specification.md`) into logical phases or milestones.
        *   Within each phase, list specific, manageable tasks required to achieve it.
        *   Use Markdown checkbox format for each task (e.g., `- [ ] Task description`).
        *   Ensure tasks are granular enough for incremental development. *Initial top-level tasks should ideally correspond to major features or phases outlined in `@specification.md`.*
    *   **`.cursorrules`**:
        *   A file containing project-specific rules for your own operation within this project.
        *   **Mandatory Rules:** Include instructions stating:
            *   "You must strictly adhere to the project requirements defined in `@specification.md`."
            *   "You must consult and update the `@tasklist.md` as you work. When a task is completed, mark its checkbox `[x]`. If new sub-tasks are identified during development, add them to the list under the relevant parent task after confirming with the user."
            *   "You must treat this `.cursorrules` file as a dynamic document. **Crucially, whenever the user provides a correction to your behavior, code, or assumptions, you MUST formulate a concise rule encapsulating that correction and add it to this file to prevent repeating the mistake.** Briefly inform the user you have added the rule."
            *   Include any specific coding style or architectural rules agreed upon during Phase 1.
        *   **Structure:** Include the mandatory rules above, followed by placeholder sections for future rules, like:
            ```
            # --- Project Specific Rules ---
            # (Mandatory rules from initialization go here)

            # --- Coding Style ---
            # (Add coding style rules here as needed)

            # --- Framework/Library Usage ---
            # (Add framework/library specific rules here)

            # --- Error Handling / Edge Cases ---
            # (Add rules related to error handling)
            ```
    *   **`README.md`**:
        *   A minimal placeholder file using Markdown format. Content should be:
            ```markdown
            # Project Title (To be filled in)

            (Project description to be added here)
            ```
3.  **Error Handling:** If you encounter any errors during file generation (e.g., permission issues, invalid content), report the specific error to the user and ask for guidance on how to proceed. Retry generation if feasible after addressing the issue.
4.  **Request Review:** After successfully generating all files, notify the user that the initial project documents (`@specification.md`, `@tasklist.md`, `@.cursorrules`, `@README.md`) have been created and explicitly ask them to review the documents for accuracy and completeness. Await their feedback before proceeding with any development tasks.

**(End of Protocol)** 