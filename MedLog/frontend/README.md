# Nuxt 3 Minimal Starter

Look at the [Nuxt 3 documentation](https://nuxt.com/docs/getting-started/introduction) to learn more.

## Setup

Make sure to install the dependencies:

```bash
# npm
npm install

# pnpm
pnpm install

# yarn
yarn install

# bun
bun install
```

## Development Server

Start the development server on `http://localhost:3000`:

```bash
# npm
npm run dev

# pnpm
pnpm run dev

# yarn
yarn dev

# bun
bun run dev
```

## Production

Build the application for production:

```bash
# npm
npm run build

# pnpm
pnpm run build

# yarn
yarn build

# bun
bun run build
```

Locally preview production build:

```bash
# npm
npm run preview

# pnpm
pnpm run preview

# yarn
yarn preview

# bun
bun run preview
```

Check out the [deployment documentation](https://nuxt.com/docs/getting-started/deployment) for more information.


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
