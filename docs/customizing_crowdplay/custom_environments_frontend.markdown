---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults
title: Custom Environments (Frontend)
nav_order: 4
layout: default
parent: Customizing CrowdPlay
---


## Custom UI Layouts and Input Options

In addition to various environment configuration options in the backend, you have the option of defining custom environment UI layouts in the frontend. For instance, one type of environment might display video output on a "TV screen"-style element, another environment might be text-based, and yet another one might show numerical output for several variables like speed, heading and altitude. CrowdPlay supports this by loading a different set of frontend UI elements depending on which environment is selected. In addition to displaying observations from the environment, the frontend UI is also used to capture user input: Layouts can include touch components like a joystick (useful for continuous action spaces), or they can load a key catcher that captures keyboard input. We provide several example layouts in `frontend/src/Enviroment/Layouts`, each of which is registered in `frontend/src/Environment/Environment.js` in the `layouts` dictionary.

Defining your own layouts is easy: Essentially a UI layout can be as simple as a chunk of HTML code with placeholders. For instance, to display a simple image observation, you could have an `<img>` element with a placeholder as the `src` attribute. The frontend would then automatically insert the jpeg-encoded image observation into the `src` attribute on each render. Doing this requires just a single line of HTML code, and a minimal amount of boilerplate Javascript code:

```jsx
export default function EnvironmentMinimalImage(props) {
  return (
    <img src={props.obsState.obs} alt="obs" />
  )
}
```

In technical terms, each layout is a React component, and gets the current observation and other state information as props. Often a simple functional component like above will be sufficient. The `obsState` object contains other state information as well, such as the current cumulative reward, which you can use to build more complex UI layouts. You can also define further configuration options in the backend that are passed into the frontend component as `props.sessionSetupDetails.ui_layout_options`.

For UI layouts that include input components such as a keycatcher or touch elements, or any other elements working with callback functions, we recommend defining these functions inside a hook function that only gets called when the UI layout is first created or using class-based components.

## Included sample layouts

We include several example layouts you can use either to render custom environments as-is, or as starting points for your own layouts.

- EnvironmentTV  displays a video output on a "TV screen"-style element. In addition, if the observation is a dictionary, and keys other than 'image' will be displayed as an HTML list to the right of the TV screen.
- EnvironmentText displays a text-based environment on a TV screen. Colored text is possible using ANSI escape codes, for instance in the Gym Taxi environment. Similarly to the video TV environment, the layout can display dictionary observations using a list for additional keys.
- EnvironmentPendulum displayes video output, and additionally features a touch joystick component for capturing continuous user input.
