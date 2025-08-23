import '@/styles/globals.css'
import Head from 'next/head'

export default function MyApp({ Component, pageProps }) {
  return (
    <>
      <Head>
        <title>Énergie & Bien-être™</title>
        <meta name="description" content="Votre dose de récupération en 8 minutes, pensée pour les soignants." />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <Component {...pageProps} />
    </>
  )
}