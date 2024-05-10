# Frontend

## Techstack

1. Nuxt3
1. Scss / Tailwind
1. Yarn as package manager

## How to setup Nuxt (required)

If not alreade installed, install the current [Node.js](https://nodejs.org/en) LTS-Version (Long time support) (recommended)

You can check if everything went as planned, by typing the following commands in your terminal:

    node -v

<br>

    example output 
    v21.02.1 

<br>

    npm -v

<br>

    example output
    9.5.1


### I recommend using [Yarn](https://classic.yarnpkg.com/en/docs/install) instead of npm as a package manager, it is faster and more secure

Yarn (v1) installation:

    npm install --global yar

Again check the installation via:

    yarn --version

For Version 3+ see the installation [here](https://v3.yarnpkg.com/getting-started/install)

## Usefull VS-Code Extensions

1. Vue - Official
1. Prettier Code formating (Optional)
1. ESLint checks Javascript/Typescript for common errors (optional)

## How to run

1. `cd Medlog/frontend`
1. `yarn` / `npm install`
1. `yarn dev` / `npm run dev`

1. Add the localhost address to the server.env file
1. Start the Server (`cd ../..`)
1. `python3 MedLog/backend/medlogserver/main.py`