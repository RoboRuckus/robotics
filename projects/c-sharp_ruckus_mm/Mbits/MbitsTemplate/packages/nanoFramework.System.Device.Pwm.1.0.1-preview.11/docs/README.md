[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=nanoframework_System.Device.Pwm&metric=alert_status)](https://sonarcloud.io/dashboard?id=nanoframework_System.Device.Pwm) [![Reliability Rating](https://sonarcloud.io/api/project_badges/measure?project=nanoframework_System.Device.Pwm&metric=reliability_rating)](https://sonarcloud.io/dashboard?id=nanoframework_System.Device.Pwm) [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![NuGet](https://img.shields.io/nuget/dt/nanoFramework.System.Device.Pwm.svg?label=NuGet&style=flat&logo=nuget)](https://www.nuget.org/packages/nanoFramework.System.Device.Pwm/) [![#yourfirstpr](https://img.shields.io/badge/first--timers--only-friendly-blue.svg)](https://github.com/nanoframework/Home/blob/main/CONTRIBUTING.md) [![Discord](https://img.shields.io/discord/478725473862549535.svg?logo=discord&logoColor=white&label=Discord&color=7289DA)](https://discord.gg/gCyBu8T)

![nanoFramework logo](https://raw.githubusercontent.com/nanoframework/Home/main/resources/logo/nanoFramework-repo-logo.png)

-----

### Welcome to the .NET **nanoFramework** System.Device.Pwm Library repository

## Build status

| Component | Build Status | NuGet Package |
|:-|---|---|
| System.Device.Pwm | [![Build Status](https://dev.azure.com/nanoframework/System.Device.Pwm/_apis/build/status/nanoframework.System.Device.Pwm?branchName=develop)](https://dev.azure.com/nanoframework/System.Device.Pwm/_build/latest?definitionId=77&branchName=main) | [![NuGet](https://img.shields.io/nuget/v/nanoFramework.System.Device.Pwm.svg?label=NuGet&style=flat&logo=nuget)](https://www.nuget.org/packages/nanoFramework.System.Device.Pwm/) |
| System.Device.Pwm (preview) | [![Build Status](https://dev.azure.com/nanoframework/System.Device.Pwm/_apis/build/status/nanoframework.System.Device.Pwm?branchName=develop)](https://dev.azure.com/nanoframework/System.Device.Pwm/_build/latest?definitionId=77&branchName=develop) | [![NuGet](https://img.shields.io/nuget/vpre/nanoFramework.System.Device.Pwm.svg?label=NuGet&style=flat&logo=nuget)](https://www.nuget.org/packages/nanoFramework.System.Device.Pwm/) |

## Usage

You can create a PWM channel from a pin number, this is the recommended way. Keep in mind, you will have to allocate the pin in the case of ESP32 and make sure your pin is PWM enabled for STM32 devices.

```csharp
// Case of ESP32, you need to set the pin function, in this example PWM3 for pin 18:
Configuration.SetPinFunction(18, DeviceFunction.PWM3);
PwmChannel pwmPin = PwmChannel.CreateFromPin(18, 40000);
// You can check then if it has created a valid one:
if (pwmPin != null)
{
    // You do have a valid one
}
```
### Duty cycle

You can adjust the duty cycle by using the property:

```csharp
pwmPin.DutyCycle = 0.42;
```

The duty cycle goes from 0.0 to 1.0.

### Frequency

It is recommended to setup the frequency when creating the PWM Channel. You can technically change it at any time but keep in mind some platform may not behave properly when adjusting this element.

### Advance PwmChannel creation

You can as well, if you know the chip/timer Id and the channel use the create function:

```csharp
PwmChannel pwmPin = new(1, 2, 40000, 0.5);
```

This is only recommended for advance users.

### Other considerations

PWM precision may vary from platform to platform. It is highly recommended to check what precision can be achieved, either with the frequency, either with the duty cycle.

## Feedback and documentation

For documentation, providing feedback, issues and finding out how to contribute please refer to the [Home repo](https://github.com/nanoframework/Home).

Join our Discord community [here](https://discord.gg/gCyBu8T).

## Credits

The list of contributors to this project can be found at [CONTRIBUTORS](https://github.com/nanoframework/Home/blob/main/CONTRIBUTORS.md).

## License

The **nanoFramework** Class Libraries are licensed under the [MIT license](LICENSE.md).

## Code of Conduct

This project has adopted the code of conduct defined by the Contributor Covenant to clarify expected behaviour in our community.
For more information see the [.NET Foundation Code of Conduct](https://dotnetfoundation.org/code-of-conduct).

### .NET Foundation

This project is supported by the [.NET Foundation](https://dotnetfoundation.org).
