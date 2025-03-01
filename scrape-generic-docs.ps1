$configArray = @(
)

$commands = @()

foreach ($config in $configArray) {
    $cmd = "python scrape.generic.docs.py --product $($config.product) --base_url $($config.base_url) --output_file $($config.output_file)"
    $commands += $cmd
}

$wtArgs = @()
$wtArgs += "-d ."
$wtArgs += $commands[0]

for ($i = 1; $i -lt $commands.Count; $i++) {
    $wtArgs += "; new-tab"
    $wtArgs += "-d ."
    $wtArgs += $commands[$i]
}

$wtArgsString = $wtArgs -join " "
Start-Process wt -ArgumentList $wtArgsString

# Loop through each configuration and open a new tab in Windows Terminal
# foreach ($config in $configArray) {
#     wt new-tab -d . -- python scrape.generic.docs.py --product $config.product --base_url $config.base_url --output_file $config.output_file
# }

<#
DONE
    @{
        product = "radix-ui-primitives"
        base_url = "https://www.radix-ui.com/primitives/docs"
        output_file = "data/radix-ui-primitives.jsonl"
    },
    @{
        product = "radix-ui-themes"
        base_url = "https://www.radix-ui.com/themes/docs"
        output_file = "data/radix-ui-themes.jsonl"
    },
    @{
        product = "shadcn-ui"
        base_url = "https://ui.shadcn.com/docs"
        output_file = "data/shadcn-ui.jsonl"
    },
    @{
        product = "shadcn-vue"
        base_url = "https://www.shadcn-vue.com/docs"
        output_file = "data/shadcn-vue.jsonl"
    },
    @{
        product = "shadcn-svelte"
        base_url = "https://www.shadcn-svelte.com/docs"
        output_file = "data/shadcn-svelte.jsonl"
    },
    @{
        product = "iconify"
        base_url = "https://iconify.design/docs"
        output_file = "data/iconify.jsonl"
    },
    @{
        product = "typescript"
        base_url = "https://www.typescriptlang.org/docs"
        output_file = "data/typescript.jsonl"
    },
    @{
        product = "tailwindcss-v3"
        base_url = "https://v3.tailwindcss.com/docs"
        output_file = "data/tailwindcss-v3.jsonl"
    },
    @{
        product = "tailwindcss"
        base_url = "https://tailwindcss.com/docs"
        output_file = "data/tailwindcss.jsonl"
    },
    @{
        product = "sass"
        base_url = "https://sass-lang.com/documentation"
        output_file = "data/sass.jsonl"
    },
    @{
        product = "postcss"
        base_url = "https://postcss.org/docs"
        output_file = "data/postcss.jsonl"
    }
    @{
        product = "biomejs-guides"
        base_url = "https://biomejs.dev/guides"
        output_file = "data/biomejs-guides.jsonl"
    },
    @{
        product = "biomejs-reference"
        base_url = "https://biomejs.dev/reference"
        output_file = "data/biomejs-reference.jsonl"
    },
    @{
        product = "biomejs-recipes"
        base_url = "https://biomejs.dev/recipes"
        output_file = "data/biomejs-recipes.jsonl"
    },
    @{
        product = "biomejs-internals"
        base_url = "https://biomejs.dev/internals"
        output_file = "data/biomejs-internals.jsonl"
    },
    @{
        product = "biomejs-analyzer"
        base_url = "https://biomejs.dev/analyzer"
        output_file = "data/biomejs-analyzer.jsonl"
    },
    @{
        product = "biomejs-formatter"
        base_url = "https://biomejs.dev/formatter"
        output_file = "data/biomejs-formatter.jsonl"
    },
    @{
        product = "biomejs-linter"
        base_url = "https://biomejs.dev/linter"
        output_file = "data/biomejs-linter.jsonl"
    },
    @{
        product = "drizzle-orm"
        base_url = "https://orm.drizzle.team/docs"
        output_file = "data/drizzle-orm.jsonl"
    },
    @{
        product = "vite-config"
        base_url = "https://vite.dev/config"
        output_file = "data/vite-config.jsonl"
    }
    @{
        product = "vite-guide"
        base_url = "https://vite.dev/guide"
        output_file = "data/vite-guide.jsonl"
    },
    @{
        product = "vite-v5-config"
        base_url = "https://v5.vite.dev/config"
        output_file = "data/vite-v5-config.jsonl"
    },
    @{
        product = "vite-v5-guide"
        base_url = "https://v5.vite.dev/guide"
        output_file = "data/vite-v5-guide.jsonl"
    },
    @{
        product = "svelte-cli"
        base_url = "https://svelte.dev/docs/cli"
        output_file = "data/svelte-cli.jsonl"
    },
    @{
        product = "svelte-kit"
        base_url = "https://svelte.dev/docs/kit"
        output_file = "data/svelte-kit.jsonl"
    },
    @{
        product = "svelte-core"
        base_url = "https://svelte.dev/docs/svelte"
        output_file = "data/svelte-core.jsonl"
    },
    @{
        product = "svelte-tutorial"
        base_url = "https://svelte.dev/tutorial/svelte"
        output_file = "data/svelte-tutorial.jsonl"
    },
    @{
        product = "react-reference"
        base_url = "https://react.dev/reference"
        output_file = "data/react-reference.jsonl"
    },
    @{
        product = "react-learn"
        base_url = "https://react.dev/learn"
        output_file = "data/react-learn.jsonl"
    },
    @{
        product = "nitro-config"
        base_url = "https://nitro.build/config"
        output_file = "data/nitro-config.jsonl"
    },
    @{
        product = "nitro-deploy"
        base_url = "https://nitro.build/deploy"
        output_file = "data/nitro-deploy.jsonl"
    },
    @{
        product = "nitro-guide"
        base_url = "https://nitro.build/guide"
        output_file = "data/nitro-guide.jsonl"
    },
    @{
        product = "nuxt"
        base_url = "https://nuxt.com/docs"
        output_file = "data/nuxt.jsonl"
    },
    @{
        product = "nuxt-modules"
        base_url = "https://nuxt.com/modules"
        output_file = "data/nuxt-modules.jsonl"
    },
    @{
        product = "nuxt-deploy"
        base_url = "https://nuxt.com/deploy"
        output_file = "data/nuxt-deploy.jsonl"
    },
    @{
        product = "nuxt-blog"
        base_url = "https://nuxt.com/blog"
        output_file = "data/nuxt-blog.jsonl"
    },
    @{
        product = "vue-api"
        base_url = "https://vuejs.org/api"
        output_file = "data/vue-api.jsonl"
    },
    @{
        product = "vue-about"
        base_url = "https://vuejs.org/about"
        output_file = "data/vue-about.jsonl"
    },
    @{
        product = "vue-guide"
        base_url = "https://vuejs.org/guide"
        output_file = "data/vue-guide.jsonl"
    },
    @{
        product = "astro"
        base_url = "https://docs.astro.build/en"
        output_file = "data/astro.jsonl"
    }
    @{
        product = "astro-case-studies"
        base_url = "https://astro.build/case-studies"
        output_file = "data/astro-case-studies.jsonl"
    },
    @{
        product = "laravel-livewire"
        base_url = "https://livewire.laravel.com/docs"
        output_file = "data/laravel-livewire.jsonl"
    },
    @{
        product = "laravel-12"
        base_url = "https://laravel.com/docs/12.x"
        output_file = "data/laravel-12.jsonl"
    },
    @{
        product = "hono"
        base_url = "https://hono.dev"
        output_file = "data/hono.jsonl"
    },
    @{
        product = "elysiajs"
        base_url = "https://elysiajs.com"
        output_file = "data/elysiajs.jsonl"
    },
    @{
        product = "caddy"
        base_url = "https://caddyserver.com/docs"
        output_file = "data/caddy.jsonl"
    },
    @{
        product = "nektosact"
        base_url = "https://nektosact.com"
        output_file = "data/nektosact.jsonl"
    },
    @{
        product = "echo"
        base_url = "https://echo.labstack.com"
        output_file = "data/echo.jsonl"
    },
    @{
        product = "podman"
        base_url = "https://podman.io/docs"
        output_file = "data/podman.jsonl"
    },
    @{
        product = "harbor-2-12-0"
        base_url = "https://goharbor.io/docs/2.12.0"
        output_file = "data/harbor-2-12-0.jsonl"
    },
    @{
        product = "asdf-vm"
        base_url = "https://asdf-vm.com"
        output_file = "data/asdf-vm.jsonl"
    },
    @{
        product = "authelia"
        base_url = "https://www.authelia.com"
        output_file = "data/authelia.jsonl"
    },
    @{
        product = "better-auth"
        base_url = "https://better-auth.vercel.app/docs"
        output_file = "data/better-auth.jsonl"
    },
    @{
        product = "skaffold"
        base_url = "https://skaffold.dev/docs"
        output_file = "data/skaffold.jsonl"
    },
    @{
        product = "templ"
        base_url = "https://templ.guide"
        output_file = "data/templ.jsonl"
    },
    @{
        product = "frankenphp"
        base_url = "https://frankenphp.dev/docs"
        output_file = "data/frankenphp.jsonl"
    }
    @{
        product = "ktor"
        base_url = "https://ktor.io/docs"
        output_file = "data/ktor.jsonl"
    },
    @{
        product = "quarkus"
        base_url = "https://quarkus.io/guides"
        output_file = "data/quarkus.jsonl"
    },
    @{
        product = "fastapi"
        base_url = "https://fastapi.tiangolo.com"
        output_file = "data/fastapi.jsonl"
    },
    @{
        product = "django-5-1"
        base_url = "https://docs.djangoproject.com/en/5.1"
        output_file = "data/django-5-1.jsonl"
    },
    @{
        product = "flask-stable"
        base_url = "https://flask.palletsprojects.com/en/stable"
        output_file = "data/flask-stable.jsonl"
    },
    @{
        product = "scrapy-latest"
        base_url = "https://docs.scrapy.org/en/latest"
        output_file = "data/scrapy-latest.jsonl"
    },
    @{
        product = "postal"
        base_url = "https://docs.postalserver.io"
        output_file = "data/postal.jsonl"
    },
    @{
        product = "rails-guides"
        base_url = "https://guides.rubyonrails.org"
        output_file = "data/rails-guides.jsonl"
    },
    @{
        product = "rails-api"
        base_url = "https://api.rubyonrails.org"
        output_file = "data/rails-api.jsonl"
    },
    @{
        product = "phoenix"
        base_url = "https://hexdocs.pm/phoenix"
        output_file = "data/phoenix.jsonl"
    }
#>
