local M = {
    {
        "mfussenegger/nvim-dap",
        dependencies = {
            "rcarriga/nvim-dap-ui",
            "mfussenegger/nvim-dap-python",
            "theHamsta/nvim-dap-virtual-text",
            "nvim-neotest/nvim-nio",
        },
        ft = {
            "python",
            "rust",
        },
        keys = {
            {
                "<leader>dt",
                function()
                    require("dapui").toggle()
                end,
                desc = "Debug: Toggle UI",
            },
            {
                "<leader>dc",
                function()
                    require("dap").continue()
                end,
                desc = "Debug: Continue",
            },
            {
                "<leader>dp",
                function()
                    require("dap").run_last()
                end,
                desc = "Debug: Run Last",
            },
            {
                "<leader>dh",
                function()
                    require("dap").step_back()
                end,
                desc = "Debug: Step Back",
            },
            {
                "<leader>dj",
                function()
                    require("dap").step_into()
                end,
                desc = "Debug: Step Into",
            },
            {
                "<leader>dk",
                function()
                    require("dap").step_out()
                end,
                desc = "Debug: Step Out",
            },
            {
                "<leader>dl",
                function()
                    require("dap").step_over()
                end,
                desc = "Debug: Step Over",
            },
            {
                "<leader>db",
                function()
                    require("dap").toggle_breakpoint()
                end,
                desc = "Debug: Toggle Breakpoint",
            },
            {
                "<leader>dB",
                function()
                    require("dap").clear_breakpoints()
                end,
                desc = "Debug: Clear Breakpoints",
            },
            {
                "<leader>dw",
                function()
                    require("dapui").elements.watches.add()
                end,
                desc = "Debug: Add Watch",
            },
            {
                "<leader>dW",
                function()
                    require("dapui").elements.watches.remove()
                end,
                desc = "Debug: Remove Watch",
            },
            {
                "<leader>dB",
                function()
                    require("dap").set_breakpoint(vim.fn.input("Breakpoint condition: "))
                end,
                desc = "Debug: Set Conditional Breakpoint",
            },
            {
                "<leader>dq",
                function()
                    require("dap").terminate()
                end,
                desc = "Debug: Terminate",
            },
        },
        config = function()
            local dap = require("dap")
            local dapui = require("dapui")

            -- Set signs
            vim.fn.sign_define(
                "DapBreakpoint",
                { text = "🔴", texthl = "DapBreakpoint", linehl = "", numhl = "" }
            )
            vim.fn.sign_define(
                "DapBreakpointCondition",
                { text = "🟠", texthl = "DapBreakpointCondition", linehl = "", numhl = "" }
            )
            vim.fn.sign_define(
                "DapLogPoint",
                { text = "📝", texthl = "DapLogPoint", linehl = "", numhl = "" }
            )
            vim.fn.sign_define("DapStopped", {
                text = "⏸️",
                texthl = "DapStopped",
                linehl = "DapStoppedLine",
                numhl = "",
            })
            vim.fn.sign_define(
                "DapBreakpointRejected",
                { text = "❌", texthl = "DapBreakpointRejected", linehl = "", numhl = "" }
            )

            -- Set up DAP UI
            dapui.setup({
                layouts = {
                    {
                        elements = {
                            { id = "scopes", size = 0.4 },
                            { id = "breakpoints", size = 0.15 },
                            { id = "stacks", size = 0.15 },
                            { id = "watches", size = 0.3 },
                        },
                        size = 50,
                        position = "left",
                    },
                    {
                        elements = {
                            { id = "repl", size = 0.5 },
                            { id = "console", size = 0.5 },
                        },
                        size = 15,
                        position = "bottom",
                    },
                },
            })

            -- Auto open/close DAP UI
            dap.listeners.after.event_initialized["dapui_config"] = function()
                dapui.open()
            end
            dap.listeners.before.event_terminated["dapui_config"] = function()
                dapui.close()
            end
            dap.listeners.before.event_exited["dapui_config"] = function()
                dapui.close()
            end

            -- Set up virtual text
            require("nvim-dap-virtual-text").setup()

            -- CodeLLDB
            dap.adapters.codelldb = {
                type = "server",
                port = "${port}",
                executable = {
                    command = "codelldb",
                    args = { "--port", "${port}" },
                },
            }

            -- Python
            require("dap-python").setup(vim.g.python3_host_prog or "python")
            dap.configurations.python = {
                {
                    type = "python",
                    request = "launch",
                    name = "Launch file",
                    program = "${file}",
                    pythonPath = function()
                        return vim.g.python3_host_prog or "python"
                    end,
                },
            }

            -- Rust
            dap.configurations.rust = {
                {
                    name = "Launch file",
                    type = "codelldb",
                    request = "launch",
                    program = function()
                        return vim.fn.input(
                            "Path to executable: ",
                            vim.fn.getcwd() .. "/target/debug/",
                            "file"
                        )
                    end,
                    cwd = "${workspaceFolder}",
                    stopOnEntry = false,
                },
            }
        end,
    },
}

return { M }
