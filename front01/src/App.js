
import './styles/App.css'

// import the socket
import React from 'react'

import { Administration } from './Administration';
import { PilotStation } from './PilotStation';
import { MapEditor } from './MapEditor';
import './styles/basic.css'
import { is_local } from './modules/configs/configs';
import { ConfigEditor } from './ConfigEditor';
import { MedicStation } from './MedicStation';
import { CommonRadarStation } from './CommonRadarStation';

import { send_command } from './modules/network/connections';
import './styles/InteractionControlWidget.css'
import './styles/Widgets.css'
import './styles/RndControlWidget.css'
import './styles/basic.css'
import './styles/AdminSystemViewer.css'
import './styles/common.css'
import './styles/ProjectileBuilderWidget.css'
import './styles/CrewControlWidget.css'
import './styles/EngineerControllerWidget.css'
import './styles/ProductionSM.css'
import './styles/ShipsDisplay.css'
import './styles/Plague.css'

import { get_http_address } from './modules/network/connections';
import { timerscounter } from './modules/utils/updatetimers';
import { get_locales } from './modules/locales/locales';
import { GameMastering } from './GameMastering';
class LoginController {
    constructor() {
        this.username = "admin"
        this.available_modules = []
    }
    login = (username) => {
        this.username = username
        this.update_available_roles()
    }

    get_username = () => {
        return this.username
    }

    is_logged = () => {
        return this.username
    }

    get_available_roles = () => {
        return this.available_modules
    }

    update_available_roles = () => {
        var myInit = {
            method: "GET",
            headers: { "username": this.username },
        }

        return fetch(get_http_address() + "/users/roles/list", myInit)
            .then(response => {
                let code = response.status;
                if (code === 200) {
                    return response.json()
                }
            }).then(data => {
                this.available_modules = data
                //console.log(this.available_modules)
            }).catch(data => {
                //console.log(data)
            })
    }
}

let loginController = new LoginController()

class LoginWindow extends React.Component {
    constructor() {
        super()
        this.state = {
            "Username": "",
            "Password": ""
        }
    }

    onLogin = () => {
        var myInit = {
            method: "GET",
            headers: this.state
        }

        return fetch(get_http_address() + "/users/login", myInit)
            .then(response => {
                let code = response.status;
                if (code === 200) {
                    return code
                }

            }).then(code => {
                if (code === 200) {
                    //console.log("login", this.state.Username)
                    loginController.login(this.state.Username)
                    send_command("ship.med_sm", "Sirocco", "log_in", { "role": this.state.Username }, true)
                    send_command("connection", "", "auth_login", { "password": this.state.Password }, true)
                    this.props.onLogin()
                }
            })
    }


    render() {
        return <div className='LoginWindow'>
            <label>username:<input onChange={(e) => { this.setState({ "Username": e.target.value }) }}></input></label>
            <label>password:<input onChange={(e) => { this.setState({ "Password": e.target.value }) }}></input></label>
            <button onClick={this.onLogin}>login</button>
        </div>
    }
}


class Navigation extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            available_modules: [],
            selected_module: "admin"
        }
    }

    componentDidMount() {
        let timer_id = timerscounter.get(this.constructor.name)
        if (!timer_id) {
            clearInterval(timer_id)
        }
        timer_id = setInterval(this.update_available_modules, 1000)
        timerscounter.add(this.constructor.name, timer_id)
    }

    componentWillUnmount() {
        let timer_id = timerscounter.get(this.constructor.name)
        clearInterval(timer_id)
    }

    update_available_modules = () => {
        loginController.update_available_roles()
        this.forceUpdate()
    }

    run_simulation = () => {
        send_command("server", null, "run", null, true)
    }

    onSelectModule = (module) => {
        this.setState({ 'selected_module': module })
        this.props.on_module_selection(module)
    }

    render() {
        let list = loginController.get_available_roles()

        if (!this.state.selected_module) {
            this.onSelectModule(list[0])
        }
        else {
            if (!list.includes(this.state.selected_module)) {
                this.onSelectModule(null)
            }
        }
        let list_nav = []
        for (let i in list) {
            let val = get_locales(list[i])
            if (list[i] === this.props.module) {
                val = <b>{get_locales(list[i])}</b>

            }

            list_nav.push(<label className="Navigation_item" onClick={() => {
                this.onSelectModule(list[i])

            }}>{val}</label>)


        }

        list_nav.push(<button
            onClick={this.props.onLogout}>
            LOGOUT
        </button>)

        /*list_nav.push(<button
         onClick={(e) => {
         send_command("server", null, "run", null, true)
         }}>
         RUN
        </button>)

       
        list_nav.push(<button
         onClick={(e) => {
         send_command("server", null, "pause", null, true)
         }}>
         PAUSE
        </button>)*/


        return (<div
            className="Navigation">
            <b>Navigation:</b>

            {list_nav}

        </div>)
    }
}


class ModuleRenderer extends React.Component {
    constructor(props) {
        super(props);
        this.state = {

        }
    }

    render() {


        switch (this.props.module) {
            case 'map_editor':
                return (<MapEditor></MapEditor>)
            case 'admin':
                return (<Administration
                    on_module_selection={this.props.on_module_selection}
                ></Administration>)


            case 'game_master':
                return (<GameMastering
                    username={loginController.get_username()}
                    on_module_selection={this.props.on_module_selection}
                ></GameMastering>)

            case 'pilot':
                return (<PilotStation
                    username={loginController.get_username()}
                    admin={true}
                ></PilotStation>)

            case 'navigator':
                return (<PilotStation
                    username={loginController.get_username()}
                    navigator={true}
                ></PilotStation>)

            case 'engineer':
                return (<PilotStation
                    username={loginController.get_username()}
                    engineer={true}
                ></PilotStation>)

            case 'cannoneer':
                return (<PilotStation
                    username={loginController.get_username()}
                    cannoneer={true}
                ></PilotStation>)

            case 'engineer_old':
                return (<PilotStation
                    username={loginController.get_username()}
                    engineer_old={true}
                ></PilotStation>)

            case 'captain':
                return (<PilotStation
                    username={loginController.get_username()}
                    captain={true}
                ></PilotStation>)

            case "config editor":
                return (<ConfigEditor key="ConfigEditor" />)

            case 'NPC_pilot':
                return (<PilotStation
                    NPC_pilot={true}
                ></PilotStation>)

            case 'medic':
                return (<MedicStation
                    username={loginController.get_username()}
                ></MedicStation>)

            case 'common_radar':
                return  (<CommonRadarStation/>)

            default:
                return (<div>
                    "Module not available"
                </div>)
        }

    }
}



class MainApp extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            "module": "config editor"
        }
    }

    on_module_selection = (module_name) => {
        this.setState({
            "module": module_name
        })
    }

    render() {
        if (is_local()) {
            if (window.location.host.split(':')[0] !== "localhost") return <div>Test NPM Server</div>
        }

        return (<div className='App'
            key="App">
            <Navigation
                onLogout={this.props.onLogout}
                module={this.state.module}
                on_module_selection={this.on_module_selection}
            >

            </Navigation>
            <ModuleRenderer
                key="ModuleRenderer"
                module={this.state.module}
                on_module_selection={this.on_module_selection}
            >
            </ModuleRenderer>
        </div>)

    }
}

class App extends React.Component {
    constructor() {
        super()
        this.state = {
            "logged": true
        }
    }
    onLogout = (e) => {
        this.setState({ "logged": false })
        send_command("ship.med_sm", "Sirocco", "log_out", { "role": loginController.get_username() }, true)
    }
    render() {
        if (this.state.logged) {
            return <MainApp onLogout={this.onLogout} />
        }
        return <LoginWindow onLogin={() => {
            this.setState({ "logged": true })
        }} />
    }
}

export default App;
